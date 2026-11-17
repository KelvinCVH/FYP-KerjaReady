"""
GET /candidate/resumes/latest: the signed-in candidate's latest resume, its status and its ratings.

Rows still at "uploading" are skipped: their file has not reached S3 (or never will, after a failed upload).
Returns {"resume": null} when there is none, otherwise the resume with:
- status: uploaded, reading, rating, done, failed or timed_out (a stalled run)
- ratings: null until the status is "done"
- view_url: a 1-hour link that opens the PDF in the browser
"""

import json
import os

import boto3
from botocore.config import Config
from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.resume_status import DONE, REPORTED_STATUS_SQL, UPLOADING

VIEW_SECONDS = 3600
# Timestamps as ISO 8601 in UTC ("2026-11-16T06:02:27Z"), so browsers parse them the same way
ISO_UTC = """to_char({} AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')"""

_s3 = None


def _client():
    """Regional endpoint, so the link points at the bucket's own region."""
    global _s3
    if _s3 is None:
        region = os.environ["AWS_REGION"]
        _s3 = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=f"https://s3.{region}.amazonaws.com",
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )
    return _s3


def view_url(s3_key):
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": os.environ["RESUME_BUCKET_NAME"], "Key": s3_key},
        ExpiresIn=VIEW_SECONDS,
    )


@api_handler
def handler(event, user):
    rows = run_query(
        f"SELECT r.resume_id, r.file_name, r.s3_key, {REPORTED_STATUS_SQL} AS status, r.failure_reason, "
        f"{ISO_UTC.format('r.uploaded_at')} AS uploaded_at, "
        "rr.a1_rating, rr.a2_rating, rr.a3_rating, rr.b2_rating, rr.a1_work_link, "
        "CAST(rr.b2_errors AS text) AS b2_errors, rr.model_version, "
        f"{ISO_UTC.format('rr.rated_at')} AS rated_at "
        "FROM resumes r LEFT JOIN resume_ratings rr USING (resume_id) "
        f"WHERE r.candidate_id = CAST(:user_id AS uuid) AND r.status <> '{UPLOADING}' "
        "ORDER BY r.resume_id DESC LIMIT 1",
        [{"name": "user_id", "value": {"stringValue": user["user_id"]}}],
    )
    if not rows:
        return 200, {"resume": None}

    row = rows[0]
    ratings = None
    if row["status"] == DONE and row.get("a1_rating") is not None:
        ratings = {
            "a1": row["a1_rating"],
            "a2": row["a2_rating"],
            "a3": row["a3_rating"],
            "b2": row["b2_rating"],
            "a1_work_link": row.get("a1_work_link"),
            "b2_errors": json.loads(row.get("b2_errors") or "[]"),
            "model_version": row["model_version"],
            "rated_at": row["rated_at"],
        }

    return 200, {
        "resume": {
            "resume_id": row["resume_id"],
            "file_name": row["file_name"],
            "status": row["status"],
            "failure_reason": row.get("failure_reason"),
            "uploaded_at": row["uploaded_at"],
            "view_url": view_url(row["s3_key"]),
            "ratings": ratings,
        }
    }