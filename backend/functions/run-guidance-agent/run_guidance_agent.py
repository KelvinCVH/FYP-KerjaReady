"""Run the guidance agent for one assessed resume and the candidate's target role, in the background (KR-97).

Two kinds of event:
- {"run_id": <id>, "output_type": "roadmap"} from POST /candidate/roadmap (KR-98), which has already created the run's
  row for its resume and role. The agent claims the row by filling in its model and prompt version, so a run is only
  ever started once.
- {"resume_id": <id>, "output_type": "roadmap" or "smoke_test"} from scripts/run_guidance_agent.py, which creates the
  row here for the candidate's current target role.

Each run's row holds its model, prompt version, tool calls, corrections and token use, then its output or why it
failed. Errors are recorded and never
re-raised, so the async invoke never retries a run. The logs hold ids and counts only, never resume text or
model output.
"""

import json
import time

import guidance_agent
import roadmap_task
import smoke_test_task
from kerjaready_shared.data_api import run_query

TASKS = {"roadmap": roadmap_task, "smoke_test": smoke_test_task}

RESUME_AND_ROLE = """
SELECT r.candidate_id, u.target_role_id AS role_id, r.status
FROM resumes r
JOIN users u ON u.user_id = r.candidate_id
WHERE r.resume_id = :resume_id
"""
# Nothing comes back when a run of this kind is already running for the resume and role (migration 012)
START_RUN = """
INSERT INTO agent_runs (candidate_id, resume_id, role_id, output_type, model_id, prompt_version)
VALUES (CAST(:candidate_id AS uuid), :resume_id, :role_id, :output_type, :model_id, :prompt_version)
ON CONFLICT DO NOTHING
RETURNING run_id
"""
# Only a row still waiting for its agent: running, with no model yet
CLAIM_RUN = """
UPDATE agent_runs SET model_id = :model_id, prompt_version = :prompt_version
WHERE run_id = :run_id AND output_type = :output_type AND status = 'running' AND model_id IS NULL
RETURNING resume_id, role_id
"""
FINISH_RUN = """
UPDATE agent_runs
SET status = 'done', output = CAST(:output AS jsonb), tool_calls = :tool_calls, corrections = :corrections,
    input_tokens = :input_tokens, output_tokens = :output_tokens, finished_at = now()
WHERE run_id = :run_id
"""
FAIL_RUN = """
UPDATE agent_runs
SET status = 'failed', error = :error, tool_calls = :tool_calls, corrections = :corrections, finished_at = now()
WHERE run_id = :run_id
"""
MAX_ERROR_CHARS = 300


def _parameters(**values):
    """Data API parameters; None becomes SQL NULL."""
    def value(item):
        if item is None:
            return {"isNull": True}
        if isinstance(item, int):
            return {"longValue": item}
        return {"stringValue": item}

    return [{"name": name, "value": value(item)} for name, item in values.items()]


def claim_run(run_id, output_type, task):
    """(run_id, resume_id, role_id) for a run POST created, or an error when it isn't waiting to start."""
    rows = run_query(CLAIM_RUN, _parameters(
        run_id=run_id,
        output_type=output_type,
        model_id=guidance_agent.model_id(),
        prompt_version=task.PROMPT_VERSION,
    ))
    if not rows:
        return {"error": "No run waiting to start with this id"}
    return run_id, rows[0]["resume_id"], rows[0]["role_id"]


def start_run(resume_id, output_type, task):
    """(run_id, resume_id, role_id) for a new run on the candidate's current target role, or an error."""
    rows = run_query(RESUME_AND_ROLE, _parameters(resume_id=resume_id))
    if not rows or rows[0]["status"] != "done":
        return {"error": "No assessed resume with this id"}
    if rows[0]["role_id"] is None:
        return {"error": "The candidate has no target role"}
    role_id = rows[0]["role_id"]

    created = run_query(START_RUN, _parameters(
        candidate_id=rows[0]["candidate_id"],
        resume_id=resume_id,
        role_id=role_id,
        output_type=output_type,
        model_id=guidance_agent.model_id(),
        prompt_version=task.PROMPT_VERSION,
    ))
    if not created:
        return {"error": "A run of this kind is already running for this resume and role"}
    return created[0]["run_id"], resume_id, role_id


def handler(event, context):
    output_type = event.get("output_type", "smoke_test")
    task = TASKS.get(output_type)
    if task is None:
        return {"error": f"Unknown output type: {output_type}"}

    if event.get("run_id") is not None:
        claimed = claim_run(int(event["run_id"]), output_type, task)
    else:
        claimed = start_run(int(event["resume_id"]), output_type, task)
    if isinstance(claimed, dict):
        print(json.dumps({"output_type": output_type, "error": claimed["error"]}))
        return claimed
    run_id, resume_id, role_id = claimed

    limit = None
    started = time.monotonic()
    try:
        run = task.prepare(resume_id, role_id)
        limit = guidance_agent.ToolCallLimit(output_tool=run.output_model.__name__)
        agent = guidance_agent.build_agent(task.SYSTEM_PROMPT, task.make_tools(resume_id, role_id), limit)
        output, input_tokens, output_tokens = guidance_agent.run_agent(agent, run.prompt, run.output_model, limit)
        output = run.finish(output)
    except Exception as error:
        message = f"{type(error).__name__}: {error}"[:MAX_ERROR_CHARS]
        tool_calls, corrections = (limit.calls, limit.corrections) if limit else (0, 0)
        run_query(FAIL_RUN, _parameters(run_id=run_id, error=message, tool_calls=tool_calls, corrections=corrections))
        print(json.dumps({"run_id": run_id, "status": "failed", "error_type": type(error).__name__,
                          "tool_calls": tool_calls, "corrections": corrections}))
        return {"run_id": run_id, "status": "failed", "error": message}

    run_query(FINISH_RUN, _parameters(
        run_id=run_id,
        output=json.dumps(output),
        tool_calls=limit.calls,
        corrections=limit.corrections,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    ))
    summary = {
        "run_id": run_id,
        "status": "done",
        "output_type": output_type,
        "tool_calls": limit.calls,
        "corrections": limit.corrections,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "seconds": round(time.monotonic() - started, 1),
    }
    print(json.dumps(summary))
    return {**summary, "output": output}