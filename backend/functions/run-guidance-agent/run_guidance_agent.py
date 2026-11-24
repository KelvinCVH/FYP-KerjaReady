"""Run the guidance agent for one assessed resume and the candidate's target role, in the background (KR-97).

Event: {"resume_id": <id>, "output_type": "smoke_test"}. Each run gets a row in agent_runs with its model,
prompt version, tool calls and token use, then its output or why it failed. Errors are recorded and never
re-raised, so the async invoke never retries a run. The logs hold ids and counts only, never resume text or
model output.
"""

import json
import time

import guidance_agent
import smoke_test_task
from kerjaready_shared.data_api import run_query

TASKS = {"smoke_test": smoke_test_task}

RESUME_AND_ROLE = """
SELECT r.candidate_id, u.target_role_id AS role_id, r.status
FROM resumes r
JOIN users u ON u.user_id = r.candidate_id
WHERE r.resume_id = :resume_id
"""
START_RUN = """
INSERT INTO agent_runs (candidate_id, resume_id, role_id, output_type, model_id, prompt_version)
VALUES (CAST(:candidate_id AS uuid), :resume_id, :role_id, :output_type, :model_id, :prompt_version)
RETURNING run_id
"""
FINISH_RUN = """
UPDATE agent_runs
SET status = 'done', output = CAST(:output AS jsonb), tool_calls = :tool_calls,
    input_tokens = :input_tokens, output_tokens = :output_tokens, finished_at = now()
WHERE run_id = :run_id
"""
FAIL_RUN = """
UPDATE agent_runs
SET status = 'failed', error = :error, tool_calls = :tool_calls, finished_at = now()
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


def handler(event, context):
    resume_id = int(event["resume_id"])
    output_type = event.get("output_type", "smoke_test")
    task = TASKS.get(output_type)
    if task is None:
        return {"error": f"Unknown output type: {output_type}"}

    rows = run_query(RESUME_AND_ROLE, _parameters(resume_id=resume_id))
    if not rows or rows[0]["status"] != "done":
        return {"error": "No assessed resume with this id"}
    if rows[0]["role_id"] is None:
        return {"error": "The candidate has no target role"}
    candidate_id, role_id = rows[0]["candidate_id"], rows[0]["role_id"]

    run_id = run_query(START_RUN, _parameters(
        candidate_id=candidate_id,
        resume_id=resume_id,
        role_id=role_id,
        output_type=output_type,
        model_id=guidance_agent.MODEL_ID,
        prompt_version=task.PROMPT_VERSION,
    ))[0]["run_id"]

    limit = guidance_agent.ToolCallLimit(output_tool=task.OutputModel.__name__)
    started = time.monotonic()
    try:
        agent = guidance_agent.build_agent(task.SYSTEM_PROMPT, task.make_tools(resume_id, role_id), limit)
        output, input_tokens, output_tokens = guidance_agent.run_agent(agent, task.build_prompt(), task.OutputModel)
    except Exception as error:
        message = f"{type(error).__name__}: {error}"[:MAX_ERROR_CHARS]
        run_query(FAIL_RUN, _parameters(run_id=run_id, error=message, tool_calls=limit.calls))
        print(json.dumps({"run_id": run_id, "status": "failed", "error_type": type(error).__name__,
                          "tool_calls": limit.calls}))
        return {"run_id": run_id, "status": "failed", "error": message}

    run_query(FINISH_RUN, _parameters(
        run_id=run_id,
        output=json.dumps(output),
        tool_calls=limit.calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    ))
    summary = {
        "run_id": run_id,
        "status": "done",
        "output_type": output_type,
        "tool_calls": limit.calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "seconds": round(time.monotonic() - started, 1),
    }
    print(json.dumps(summary))
    return {**summary, "output": output}