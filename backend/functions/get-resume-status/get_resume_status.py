"""
GET /candidate/resumes/{resume_id}/status: the assessment status of one of the signed-in candidate's resumes.

Returns {"status", "failure_reason"}. status is uploaded, reading, rating, done, failed or timed_out.
timed_out is worked out by the database clock. Another candidate's resume, or a missing one, gives 404.
"""

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.resume_status import REPORTED_STATUS_SQL

NOT_FOUND = {"message": "We couldn’t find that resume."}


def read_resume_id(event):
    """The resume id from the path, or None when it is not a whole number."""
    value = (event.get("pathParameters") or {}).get("resume_id", "")
    return int(value) if value.isdigit() else None


@api_handler
def handler(event, user):
    resume_id = read_resume_id(event)
    if resume_id is None:
        return 404, NOT_FOUND

    rows = run_query(
        f"SELECT {REPORTED_STATUS_SQL} AS status, failure_reason FROM resumes "
        "WHERE resume_id = :resume_id AND candidate_id = CAST(:user_id AS uuid)",
        [
            {"name": "resume_id", "value": {"longValue": resume_id}},
            {"name": "user_id", "value": {"stringValue": user["user_id"]}},
        ],
    )
    if not rows:
        return 404, NOT_FOUND

    return 200, {"status": rows[0]["status"], "failure_reason": rows[0].get("failure_reason")}
