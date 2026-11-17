"""
Resume assessment status, shared by the pipeline and the resume routes.

Stored values, in order:
uploading (row created, file not in S3 yet) -> uploaded -> reading -> rating -> done, or failed.
timed_out is never stored. It is reported when a running status has not changed for STALE_AFTER_SECONDS.
Every UPDATE that changes the status must also set status_updated_at = NOW(), or the run looks stalled.
"""

from kerjaready_shared.data_api import run_query

UPLOADING = "uploading"
UPLOADED = "uploaded"
READING = "reading"
RATING = "rating"
DONE = "done"
FAILED = "failed"
TIMED_OUT = "timed_out"

# Statuses of a run that has not finished. Each one can stall, so each one can time out.
RUNNING = (UPLOADING, UPLOADED, READING, RATING)

# Must stay above the process-resume timeout, so a run reported as timed out has really stopped
STALE_AFTER_SECONDS = 120

# failure_reason codes. Only "error" is worth a retry: the same file fails the same way for the others.
NOT_PDF = "not_pdf"
NO_TEXT = "no_text"
ERROR = "error"

_RUNNING_SQL = ", ".join(f"'{status}'" for status in RUNNING)

# SQL condition: a running status that has not changed for too long, by the database clock
STALE_SQL = (
    f"(status IN ({_RUNNING_SQL}) "
    f"AND status_updated_at < NOW() - make_interval(secs => {STALE_AFTER_SECONDS}))"
)

# SQL condition: a run the candidate may start again
RETRYABLE_SQL = f"((status = '{FAILED}' AND failure_reason = '{ERROR}') OR {STALE_SQL})"

# SQL expression for the status the app sees: timed_out when stale, and uploading shown as uploaded
REPORTED_STATUS_SQL = (
    f"CASE WHEN {STALE_SQL} THEN '{TIMED_OUT}' "
    f"WHEN status = '{UPLOADING}' THEN '{UPLOADED}' "
    "ELSE status END"
)


def set_status(resume_id, status, failure_reason=None):
    """Move a resume to a new status and restart its stale clock."""
    run_query(
        "UPDATE resumes SET status = :status, failure_reason = :failure_reason, status_updated_at = NOW() "
        "WHERE resume_id = :resume_id",
        [
            {"name": "status", "value": {"stringValue": status}},
            {
                "name": "failure_reason",
                "value": {"isNull": True} if failure_reason is None else {"stringValue": failure_reason},
            },
            {"name": "resume_id", "value": {"longValue": resume_id}},
        ],
    )
