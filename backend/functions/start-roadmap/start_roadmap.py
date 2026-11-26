"""
POST /candidate/roadmap: start writing a learning roadmap for the candidate's latest assessed resume and target role
(KR-98).

The run's row is created here, before the agent starts, so the page sees it straight away. A partial unique index
allows one running run per resume and role, so a double click or two tabs start only one: the second POST gets the
run already in progress. A run stuck at running (kerjaready_shared/roadmap_runs.py) is closed first, so Try Again
works after a stalled run. The agent then runs in the background with this run's id.

- 202 with the run (status running): a new one, or the one already in progress
- 409 when there is no assessed resume or no target role
"""

import json
import os

import boto3
from kerjaready_shared import roadmap_runs
from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query

NO_RESUME = {"message": "Your learning roadmap starts from an assessed resume."}
NO_ROLE = {"message": "Choose a target role on your Profile first."}

CLOSE_STALE = f"""
UPDATE agent_runs
SET status = '{roadmap_runs.FAILED}', error = 'Stopped before it finished', finished_at = NOW()
WHERE resume_id = :resume_id AND role_id = :role_id AND output_type = '{roadmap_runs.ROADMAP}'
  AND {roadmap_runs.STALE_RUN_SQL}
"""
# The model and prompt version are filled in by the agent when it starts
CREATE_RUN = f"""
INSERT INTO agent_runs (candidate_id, resume_id, role_id, output_type)
VALUES (CAST(:user_id AS uuid), :resume_id, :role_id, '{roadmap_runs.ROADMAP}')
ON CONFLICT DO NOTHING
RETURNING run_id
"""
FAIL_START = f"""
UPDATE agent_runs
SET status = '{roadmap_runs.FAILED}', error = 'The agent could not be started', finished_at = NOW()
WHERE run_id = :run_id
"""

_lambda = None


def _client():
    global _lambda
    if _lambda is None:
        _lambda = boto3.client("lambda")
    return _lambda


@api_handler
def handler(event, user):
    resume, role = roadmap_runs.context(user["user_id"])
    if resume is None:
        return 409, NO_RESUME
    if role is None:
        return 409, NO_ROLE

    parameters = roadmap_runs.resume_and_role_parameters(resume, role)
    run_query(CLOSE_STALE, parameters)
    created = run_query(CREATE_RUN, [roadmap_runs.user_parameter(user["user_id"]), *parameters])
    if created:
        run_id = created[0]["run_id"]
        try:
            _client().invoke(
                FunctionName=os.environ["GUIDANCE_FUNCTION_NAME"],
                InvocationType="Event",
                Payload=json.dumps({"run_id": run_id, "output_type": roadmap_runs.ROADMAP}).encode("utf-8"),
            )
        except Exception:
            run_query(FAIL_START, [{"name": "run_id", "value": {"longValue": run_id}}])
            raise

    return 202, {"run": roadmap_runs.run_summary(roadmap_runs.latest_run(resume, role))}