"""
POST /candidate/resumes/{resume_id}/retry: start the assessment again on the same resume.

Allowed when it failed with "error", or when it has stalled (timed out). One conditional UPDATE resets it to
uploaded, so a double click or two tabs can start only one run. Then process-resume is invoked in the background.
202 when started, 409 when the run can't be retried now, 404 for another candidate's resume or a missing one.
"""

import json
import os

import boto3
from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.resume_status import RETRYABLE_SQL, UPLOADED

NOT_FOUND = {"message": "We couldn’t find that resume."}
NOT_RETRYABLE = {"message": "This assessment can’t be started again right now."}

_lambda = None


def _client():
    global _lambda
    if _lambda is None:
        _lambda = boto3.client("lambda")
    return _lambda


def read_resume_id(event):
    """The resume id from the path, or None when it is not a whole number."""
    value = (event.get("pathParameters") or {}).get("resume_id", "")
    return int(value) if value.isdigit() else None


@api_handler
def handler(event, user):
    resume_id = read_resume_id(event)
    if resume_id is None:
        return 404, NOT_FOUND

    parameters = [
        {"name": "resume_id", "value": {"longValue": resume_id}},
        {"name": "user_id", "value": {"stringValue": user["user_id"]}},
    ]
    claimed = run_query(
        f"UPDATE resumes SET status = '{UPLOADED}', failure_reason = NULL, status_updated_at = NOW() "
        f"WHERE resume_id = :resume_id AND candidate_id = CAST(:user_id AS uuid) AND {RETRYABLE_SQL} "
        "RETURNING resume_id",
        parameters,
    )
    if not claimed:
        owned = run_query(
            "SELECT resume_id FROM resumes WHERE resume_id = :resume_id AND candidate_id = CAST(:user_id AS uuid)",
            parameters,
        )
        return (409, NOT_RETRYABLE) if owned else (404, NOT_FOUND)

    # If this call fails, the row stays uploaded and is reported as timed out later, so Retry works again
    _client().invoke(
        FunctionName=os.environ["PROCESS_FUNCTION_NAME"],
        InvocationType="Event",
        Payload=json.dumps({"resume_id": resume_id}).encode("utf-8"),
    )
    return 202, {"status": UPLOADED, "failure_reason": None}
