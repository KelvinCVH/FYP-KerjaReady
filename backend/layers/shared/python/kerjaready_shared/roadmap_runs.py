"""Roadmap runs, shared by GET and POST /candidate/roadmap (KR-98).

A roadmap is written for the candidate's latest assessed resume and their current target role, and each run is a row
in agent_runs with output_type 'roadmap'. POST creates the row before it starts the agent, so the page never sees a
started run go missing, and a partial unique index (migration 012) allows one running run per resume, role and output
type.

The agent Lambda stops after 5 minutes. A run still 'running' after STALE_AFTER_SECONDS has stopped without saying so:
GET reports it as failed, and POST closes it before it starts a new one.
"""

from kerjaready_shared.data_api import run_query

ROADMAP = "roadmap"
RUNNING = "running"
DONE = "done"
FAILED = "failed"

# Must stay above the run-guidance-agent timeout (5 minutes), so a run reported as failed has really stopped
STALE_AFTER_SECONDS = 360

# SQL condition: a run still marked running that must have stopped, by the database clock
STALE_RUN_SQL = (
    f"(status = '{RUNNING}' AND created_at < NOW() - make_interval(secs => {STALE_AFTER_SECONDS}))"
)
# SQL expression for the status the page sees
REPORTED_RUN_STATUS_SQL = f"CASE WHEN {STALE_RUN_SQL} THEN '{FAILED}' ELSE status END"

# Timestamps as ISO 8601 in UTC ("2026-11-26T01:10:22Z"), so browsers parse them the same way
ISO_UTC = """to_char({} AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')"""

# The candidate's target role with its posting count, and their latest resume whose assessment finished.
# Resumes still being assessed are skipped, so the roadmap stays on the last assessed one until the new one is done.
CONTEXT = f"""
SELECT u.target_role_id AS role_id, ro.title,
       (SELECT count(*) FROM job_postings jp WHERE jp.role_id = u.target_role_id) AS posting_count,
       latest.resume_id, latest.file_name, {ISO_UTC.format('latest.rated_at')} AS assessed_at
FROM users u
LEFT JOIN roles ro ON ro.role_id = u.target_role_id
LEFT JOIN LATERAL (
    SELECT r.resume_id, r.file_name, rr.rated_at
    FROM resumes r
    JOIN resume_ratings rr ON rr.resume_id = r.resume_id
    WHERE r.candidate_id = u.user_id AND r.status = 'done'
    ORDER BY r.resume_id DESC
    LIMIT 1
) latest ON true
WHERE u.user_id = CAST(:user_id AS uuid)
"""

LATEST_RUN = f"""
SELECT run_id, {REPORTED_RUN_STATUS_SQL} AS status,
       {ISO_UTC.format('created_at')} AS created_at, {ISO_UTC.format('finished_at')} AS finished_at,
       CAST(output AS text) AS output
FROM agent_runs
WHERE resume_id = :resume_id AND role_id = :role_id AND output_type = '{ROADMAP}'
ORDER BY created_at DESC, run_id DESC
LIMIT 1
"""


def user_parameter(user_id):
    return {"name": "user_id", "value": {"stringValue": user_id}}


def resume_and_role_parameters(resume, role):
    return [
        {"name": "resume_id", "value": {"longValue": resume["resume_id"]}},
        {"name": "role_id", "value": {"longValue": role["role_id"]}},
    ]


def context(user_id):
    """(resume, target role) for the candidate. Either is None when there is none."""
    rows = run_query(CONTEXT, [user_parameter(user_id)])
    row = rows[0] if rows else {}
    resume = None
    if row.get("resume_id") is not None:
        resume = {"resume_id": row["resume_id"], "file_name": row["file_name"], "assessed_at": row["assessed_at"]}
    role = None
    if row.get("role_id") is not None:
        role = {"role_id": row["role_id"], "title": row["title"], "posting_count": row["posting_count"]}
    return resume, role


def latest_run(resume, role):
    """The newest roadmap run for this resume and role, with its output as JSON text, or None."""
    rows = run_query(LATEST_RUN, resume_and_role_parameters(resume, role))
    return rows[0] if rows else None


def run_summary(row):
    return {
        "run_id": row["run_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "finished_at": row.get("finished_at"),
    }