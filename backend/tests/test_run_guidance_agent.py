import json
import sys
from types import SimpleNamespace

import pytest

from conftest import FUNCTIONS_DIR, USER_ID, FakeDatabase

# The function is several modules: put its folder on the path, as Lambda does
sys.path.insert(0, str(FUNCTIONS_DIR / "run-guidance-agent"))
import guidance_agent  # noqa: E402
import roadmap_task  # noqa: E402
import run_guidance_agent  # noqa: E402
import smoke_test_task  # noqa: E402

ASSESSED = {"candidate_id": USER_ID, "role_id": 4, "status": "done"}
MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"


@pytest.fixture(autouse=True)
def guidance_model(monkeypatch):
    """The stack sets the model; the tests set the one it uses today."""
    monkeypatch.setenv("GUIDANCE_MODEL_ID", MODEL_ID)
OUTPUT = {
    "role_title": "AI/ML Engineer",
    "lowest_criterion": "Outcome",
    "top_skills_not_evidenced": ["TensorFlow", "REST API", "Microsoft Azure"],
    "top_skill_reason": "AI/ML Engineer postings ask for TensorFlow to train deep learning models.",
    "source_posting_ids": [901],
    "summary": "AI/ML Engineer; Outcome is lowest; TensorFlow, REST API and Microsoft Azure are not evidenced.",
}


def database_with(resume_row=ASSESSED):
    def answer(sql, params):
        if "FROM resumes r" in sql:
            return [resume_row] if resume_row else []
        if sql.strip().startswith("INSERT INTO agent_runs"):
            return [{"run_id": 77}]
        return []
    return FakeDatabase(answer)


@pytest.fixture
def agent_calls(monkeypatch):
    """Replace the model with a stand-in that records how it was called."""
    calls = {}

    def build_agent(system_prompt, tools, limit):
        calls["system_prompt"], calls["tools"] = system_prompt, tools
        return "agent"

    def run_agent(agent, prompt, output_model, limit):
        calls["prompt"], calls["output_model"] = prompt, output_model
        if "error" in calls:
            raise calls["error"]
        return OUTPUT, 1200, 80

    monkeypatch.setattr(guidance_agent, "build_agent", build_agent)
    monkeypatch.setattr(guidance_agent, "run_agent", run_agent)
    return calls


def call(monkeypatch, database, event=None):
    monkeypatch.setattr(run_guidance_agent, "run_query", database)
    return run_guidance_agent.handler(event or {"resume_id": 9, "output_type": "smoke_test"}, None)


def test_a_run_is_recorded_with_its_model_output_and_usage(monkeypatch, agent_calls):
    database = database_with()
    result = call(monkeypatch, database)

    assert result["run_id"] == 77 and result["status"] == "done"
    assert result["output"] == OUTPUT
    (_, lookup), (start_sql, start), (finish_sql, finish) = database.queries
    assert lookup == {"resume_id": 9}
    assert start == {
        "candidate_id": USER_ID, "resume_id": 9, "role_id": 4, "output_type": "smoke_test",
        "model_id": MODEL_ID, "prompt_version": "smoke-test-v3",
    }
    assert "status = 'done'" in finish_sql
    assert json.loads(finish["output"]) == OUTPUT
    assert finish["input_tokens"] == 1200 and finish["output_tokens"] == 80
    assert finish["tool_calls"] == 0 and finish["corrections"] == 0
    assert agent_calls["prompt"] == smoke_test_task.PROMPT
    assert agent_calls["output_model"] is smoke_test_task.OutputModel
    assert [t.tool_name for t in agent_calls["tools"]] == ["get_assessment_ratings", "get_skill_gap", "get_market_context"]


def test_a_failed_run_is_recorded_and_not_raised(monkeypatch, agent_calls):
    agent_calls["error"] = RuntimeError("model refused")
    database = database_with()
    result = call(monkeypatch, database)

    assert result == {"run_id": 77, "status": "failed", "error": "RuntimeError: model refused"}
    fail_sql, fail = database.queries[-1]
    assert "status = 'failed'" in fail_sql
    assert fail == {"run_id": 77, "error": "RuntimeError: model refused", "tool_calls": 0, "corrections": 0}


def test_a_run_that_fails_before_the_agent_starts_is_recorded(monkeypatch, agent_calls):
    def no_role(resume_id, role_id):
        raise ValueError("The target role was not found.")

    monkeypatch.setattr(roadmap_task, "prepare", no_role)
    database = database_with()
    result = call(monkeypatch, database, {"resume_id": 9, "output_type": "roadmap"})

    assert result == {"run_id": 77, "status": "failed", "error": "ValueError: The target role was not found."}
    assert database.queries[-1][1]["tool_calls"] == 0 and database.queries[-1][1]["corrections"] == 0
    assert "prompt" not in agent_calls


@pytest.mark.parametrize("resume_row, message", [
    (None, "No assessed resume with this id"),
    ({**ASSESSED, "status": "rating"}, "No assessed resume with this id"),
    ({**ASSESSED, "role_id": None}, "The candidate has no target role"),
])
def test_no_run_starts_without_an_assessed_resume_and_a_target_role(monkeypatch, agent_calls, resume_row, message):
    database = database_with(resume_row)
    assert call(monkeypatch, database) == {"error": message}
    assert len(database.queries) == 1
    assert "prompt" not in agent_calls


def test_a_roadmap_run_uses_the_runs_prompt_and_schema_and_saves_the_finished_output(monkeypatch, agent_calls):
    roadmap = roadmap_task.output_model_for(["TensorFlow"])
    monkeypatch.setattr(roadmap_task, "prepare", lambda resume_id, role_id: guidance_agent.TaskRun(
        "Roadmap prompt.", roadmap, finish=lambda output: {"finished": output["role_title"]}))
    database = database_with()
    result = call(monkeypatch, database, {"resume_id": 9, "output_type": "roadmap"})

    _, start = database.queries[1]
    assert start["output_type"] == "roadmap" and start["prompt_version"] == "roadmap-v5"
    assert agent_calls["system_prompt"] == roadmap_task.SYSTEM_PROMPT
    assert agent_calls["prompt"] == "Roadmap prompt." and agent_calls["output_model"] is roadmap
    assert result["output"] == {"finished": "AI/ML Engineer"}
    assert json.loads(database.queries[-1][1]["output"]) == {"finished": "AI/ML Engineer"}


def test_an_unknown_output_type_is_refused(monkeypatch, agent_calls):
    database = database_with()
    assert call(monkeypatch, database, {"resume_id": 9, "output_type": "essay"}) == {
        "error": "Unknown output type: essay"
    }
    assert database.queries == []


def tool_call(name):
    return SimpleNamespace(tool_use={"name": name, "input": {}}, cancel_tool=False)


def test_tool_calls_after_the_limit_are_cancelled():
    limit = guidance_agent.ToolCallLimit(output_tool="OutputModel", max_calls=2)
    events = [tool_call("get_skill_gap") for _ in range(3)]
    for event in events:
        limit.count(event)
    assert [e.cancel_tool for e in events[:2]] == [False, False]
    assert events[2].cancel_tool.startswith("Tool call limit reached: a run may make at most 2 tool calls.")

    limit.reset(None)
    assert limit.calls == 0


def rejection(name, status):
    return SimpleNamespace(tool_use={"name": name}, result={"status": status, "content": [{"text": "Fix: brackets."}]})


def test_rejected_outputs_are_counted_as_corrections():
    limit = guidance_agent.ToolCallLimit(output_tool="Roadmap")
    for event in [rejection("Roadmap", "error"), rejection("get_skill_gap", "error"), rejection("Roadmap", "error"),
                  rejection("Roadmap", "success")]:
        limit.record_rejection(event)
    assert limit.corrections == 2 and limit.last_rejection == "Fix: brackets."

    limit.reset(None)
    assert limit.corrections == 0 and limit.last_rejection is None


def test_the_structured_output_call_is_never_counted_or_cancelled():
    limit = guidance_agent.ToolCallLimit(output_tool="OutputModel", max_calls=1)
    limit.count(tool_call("get_skill_gap"))
    output = tool_call("OutputModel")
    limit.count(output)
    assert output.cancel_tool is False
    assert limit.calls == 1


def test_the_agent_uses_the_stacks_model_through_converse():
    limit = guidance_agent.ToolCallLimit(output_tool="OutputModel")
    agent = guidance_agent.build_agent("System.", smoke_test_task.make_tools(9, 4), limit)

    assert agent.model.config["model_id"] == MODEL_ID
    assert agent.model.config["streaming"] is False
    assert agent.tool_names == ["get_assessment_ratings", "get_skill_gap", "get_market_context"]


def test_run_agent_returns_the_output_and_token_use_and_caps_corrections():
    reply = smoke_test_task.OutputModel(**OUTPUT)
    usage = SimpleNamespace(accumulated_usage={"inputTokens": 1200, "outputTokens": 80, "totalTokens": 1280})
    result = SimpleNamespace(structured_output=reply, metrics=usage, stop_reason="end_turn")
    limit = guidance_agent.ToolCallLimit(output_tool="OutputModel")
    calls = []

    def agent(prompt, **kwargs):
        calls.append(kwargs)
        return result

    assert guidance_agent.run_agent(agent, "Prompt.", smoke_test_task.OutputModel, limit) == (OUTPUT, 1200, 80)
    assert calls[0]["limits"] == {"structured_output_attempts": 3}

    empty = SimpleNamespace(structured_output=None, metrics=usage, stop_reason="end_turn")
    with pytest.raises(ValueError, match="no structured output"):
        guidance_agent.run_agent(lambda prompt, **kwargs: empty, "Prompt.", smoke_test_task.OutputModel, limit)


def test_run_agent_fails_with_the_last_rejection_once_corrections_run_out():
    limit = guidance_agent.ToolCallLimit(output_tool="OutputModel")
    limit.corrections, limit.last_rejection = 3, "Fix: brackets."
    stopped = SimpleNamespace(structured_output=None, metrics=None, stop_reason="limit_structured_output_attempts")
    with pytest.raises(ValueError, match="failed its checks 3 times. Fix: brackets."):
        guidance_agent.run_agent(lambda prompt, **kwargs: stopped, "Prompt.", smoke_test_task.OutputModel, limit)