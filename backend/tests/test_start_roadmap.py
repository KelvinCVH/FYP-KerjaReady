import json

import pytest

from conftest import USER_ID, FakeDatabase, load_function

start_roadmap = load_function("start-roadmap")
ROUTE = "POST /candidate/roadmap"

CONTEXT_ROW = {"role_id": 4, "title": "AI/ML Engineer", "posting_count": 52,
               "resume_id": 331, "file_name": "Resume_v3.pdf", "assessed_at": "2026-11-17T08:12:00Z"}
RUNNING = {"run_id": 210, "status": "running", "created_at": "2026-11-26T04:00:00Z", "finished_at": None,
           "output": None}


class FakeLambda:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"StatusCode": 202}


@pytest.fixture
def lambda_client(monkeypatch):
    client = FakeLambda()
    monkeypatch.setenv("GUIDANCE_FUNCTION_NAME", "kerjaready-run-guidance-agent")
    monkeypatch.setattr(start_roadmap, "_lambda", client)
    return client


def database_with(context=CONTEXT_ROW, created=True):
    def answer(sql, params):
        if "FROM users u" in sql:
            return [context]
        if sql.strip().startswith("INSERT INTO agent_runs"):
            return [{"run_id": 210}] if created else []
        if "FROM agent_runs" in sql:
            return [RUNNING]
        return []
    return FakeDatabase(answer)


def call(monkeypatch, database):
    monkeypatch.setattr(start_roadmap.roadmap_runs, "run_query", database)
    monkeypatch.setattr(start_roadmap, "run_query", database)
    claims = {"sub": USER_ID, "cognito:groups": "[candidate]"}
    response = start_roadmap.handler({"routeKey": ROUTE, "requestContext": {"authorizer": {"jwt": {"claims": claims}}}},
                                     None)
    return response["statusCode"], json.loads(response["body"])


def statements(database):
    return [sql.strip().split("\n")[0] for sql, _ in database.queries]


def test_a_new_run_is_created_then_the_agent_starts_with_its_id(monkeypatch, lambda_client):
    database = database_with()
    status, body = call(monkeypatch, database)

    assert status == 202
    assert body == {"run": {"run_id": 210, "status": "running", "created_at": "2026-11-26T04:00:00Z",
                            "finished_at": None}}
    _, close, (create_sql, create), _ = database.queries
    assert create == {"user_id": USER_ID, "resume_id": 331, "role_id": 4}
    assert "ON CONFLICT DO NOTHING" in create_sql and "'roadmap'" in create_sql
    assert "model_id" not in create_sql
    [invoke] = lambda_client.calls
    assert invoke["FunctionName"] == "kerjaready-run-guidance-agent" and invoke["InvocationType"] == "Event"
    assert json.loads(invoke["Payload"]) == {"run_id": 210, "output_type": "roadmap"}


def test_a_stuck_run_is_closed_before_a_new_one_is_created(monkeypatch, lambda_client):
    database = database_with()
    call(monkeypatch, database)

    (close_sql, close), (create_sql, _) = database.queries[1:3]
    assert close_sql.strip().startswith("UPDATE agent_runs")
    assert "status = 'failed'" in close_sql
    assert "(status = 'running' AND created_at < NOW() - make_interval(secs => 360))" in close_sql
    assert close == {"resume_id": 331, "role_id": 4}
    assert create_sql.strip().startswith("INSERT INTO agent_runs")


def test_a_run_already_in_progress_is_returned_without_starting_another(monkeypatch, lambda_client):
    database = database_with(created=False)
    status, body = call(monkeypatch, database)

    assert status == 202 and body["run"]["run_id"] == 210 and body["run"]["status"] == "running"
    assert lambda_client.calls == []


def test_a_run_whose_agent_cannot_be_started_is_marked_failed(monkeypatch):
    client = FakeLambda(error=RuntimeError("throttled"))
    monkeypatch.setenv("GUIDANCE_FUNCTION_NAME", "kerjaready-run-guidance-agent")
    monkeypatch.setattr(start_roadmap, "_lambda", client)
    database = database_with()
    status, _ = call(monkeypatch, database)

    assert status == 500
    fail_sql, fail = database.queries[-1]
    assert "status = 'failed'" in fail_sql and "could not be started" in fail_sql
    assert fail == {"run_id": 210}


@pytest.mark.parametrize("context, message", [
    ({**CONTEXT_ROW, "resume_id": None, "file_name": None, "assessed_at": None},
     "Your learning roadmap starts from an assessed resume."),
    ({**CONTEXT_ROW, "role_id": None, "title": None, "posting_count": 0},
     "Choose a target role on your Profile first."),
])
def test_no_run_without_an_assessed_resume_and_a_target_role(monkeypatch, lambda_client, context, message):
    database = database_with(context=context)
    status, body = call(monkeypatch, database)

    assert (status, body) == (409, {"message": message})
    assert len(database.queries) == 1 and lambda_client.calls == []