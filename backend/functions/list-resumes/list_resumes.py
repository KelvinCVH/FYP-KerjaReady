"""
GET /candidate/resumes: the signed-in candidate's resume assessments, newest first.

Rows still at "uploading" are left out: their file is not in S3 yet, or never arrived after a failed upload.
Returns {"resumes": [{"resume_id", "file_name", "uploaded_at", "status", "failure_reason"}, ...]}, at most 50.
status is uploaded, reading, rating, done, failed or timed_out, as on the status route.
"""

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.resume_status import REPORTED_STATUS_SQL, UPLOADING

LIMIT = 50
# Timestamps as ISO 8601 in UTC ("2026-11-16T06:02:27Z"), so browsers parse them the same way
ISO_UTC = """to_char({} AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')"""


@api_handler
def handler(event, user):
    rows = run_query(
        f"SELECT resume_id, file_name, {ISO_UTC.format('uploaded_at')} AS uploaded_at, "
        f"{REPORTED_STATUS_SQL} AS status, failure_reason "
        "FROM resumes "
        f"WHERE candidate_id = CAST(:user_id AS uuid) AND status <> '{UPLOADING}' "
        f"ORDER BY resume_id DESC LIMIT {LIMIT}",
        [{"name": "user_id", "value": {"stringValue": user["user_id"]}}],
    )
    return 200, {
        "resumes": [
            {
                "resume_id": row["resume_id"],
                "file_name": row["file_name"],
                "uploaded_at": row["uploaded_at"],
                "status": row["status"],
                "failure_reason": row.get("failure_reason"),
            }
            for row in rows
        ]
    }