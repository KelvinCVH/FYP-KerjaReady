"""
Rate an uploaded resume in the background. S3 starts this function for each new PDF under resumes/.

1. Claim the resume row: uploading -> assessing. A repeated S3 event finds nothing to claim.
2. kerjaready-assess-resume reads the PDF. The text is saved on the resume row.
3. kerjaready-assess-resume rates the text. The ratings are saved in resume_ratings.
4. Status done, or failed with failure_reason not_pdf, no_text or error.
"""

import json
import os
import traceback
import urllib.parse

import boto3
from botocore.config import Config
from kerjaready_shared.data_api import run_query

# A first call can take about a minute while the assessment container starts.
# Never retry the call: a retry would start a second container and rate the resume twice.
LAMBDA_CONFIG = Config(read_timeout=150, retries={"total_max_attempts": 1})

_lambda = None


def _client():
    global _lambda
    if _lambda is None:
        _lambda = boto3.client("lambda", config=LAMBDA_CONFIG)
    return _lambda


def _parameters(**values):
    """Data API parameters; None becomes SQL NULL."""
    def value(item):
        if item is None:
            return {"isNull": True}
        if isinstance(item, int):
            return {"longValue": item}
        return {"stringValue": item}

    return [{"name": name, "value": value(item)} for name, item in values.items()]


def assess(payload):
    """Call kerjaready-assess-resume and return its answer."""
    response = _client().invoke(
        FunctionName=os.environ["ASSESS_FUNCTION_NAME"],
        Payload=json.dumps(payload).encode("utf-8"),
    )
    body = json.loads(response["Payload"].read() or b"null")
    if response.get("FunctionError"):
        error_type = body.get("errorType") if isinstance(body, dict) else None
        raise RuntimeError(f"kerjaready-assess-resume failed: {error_type}")
    return body


def set_status(resume_id, status, failure_reason=None):
    run_query(
        "UPDATE resumes SET status = :status, failure_reason = :failure_reason WHERE resume_id = :resume_id",
        _parameters(status=status, failure_reason=failure_reason, resume_id=resume_id),
    )


def save_ratings(resume_id, ratings):
    run_query(
        "INSERT INTO resume_ratings "
        "(resume_id, a1_rating, a2_rating, a3_rating, b2_rating, a1_work_link, b2_errors, model_version) "
        "VALUES (:resume_id, :a1, :a2, :a3, :b2, :a1_work_link, CAST(:b2_errors AS jsonb), :model_version) "
        "ON CONFLICT (resume_id) DO NOTHING",
        _parameters(
            resume_id=resume_id,
            a1=ratings["a1"],
            a2=ratings["a2"],
            a3=ratings["a3"],
            b2=ratings["b2"],
            a1_work_link=ratings.get("a1_work_link"),
            b2_errors=json.dumps(ratings.get("b2_errors") or []),
            model_version=ratings["model_version"],
        ),
    )


def process(bucket, key):
    claimed = run_query(
        "UPDATE resumes SET status = 'assessing' WHERE s3_key = :s3_key AND status = 'uploading' RETURNING resume_id",
        _parameters(s3_key=key),
    )
    if not claimed:
        print(json.dumps({"skipped": "no resume is waiting for this upload"}))
        return
    resume_id = claimed[0]["resume_id"]

    try:
        extracted = assess({"action": "extract", "bucket": bucket, "key": key})
        if extracted.get("error"):
            set_status(resume_id, "failed", extracted["error"])
            print(json.dumps({"resume_id": resume_id, "status": "failed", "reason": extracted["error"]}))
            return

        run_query(
            "UPDATE resumes SET extracted_text = :text WHERE resume_id = :resume_id",
            _parameters(text=extracted["text"], resume_id=resume_id),
        )
        ratings = assess({"text": extracted["text"], "pdf_links": extracted.get("pdf_links") or []})
        save_ratings(resume_id, ratings)
        set_status(resume_id, "done")
        print(json.dumps({"resume_id": resume_id, "status": "done"}))
    except Exception:
        traceback.print_exc()
        set_status(resume_id, "failed", "error")
        raise


def handler(event, context=None):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        process(bucket, key)