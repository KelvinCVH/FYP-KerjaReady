import json

import pytest

from conftest import USER_ID, FakeDatabase, candidate_event, load_function

retry_resume_assessment = load_function("retry-resume-assessment")
ROUTE = "POST /candidate/resumes/{resume_id}/retry"


class FakeLambda:
    def __init__(self):
        self.calls = []

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        return {"StatusCode": 202}


@pytest.fixture
def lambda_client(monkeypatch):
    client = FakeLambda()
    monkeypatch.setenv("PROCESS_FUNCTION_NAME", "kerjaready-process-resume")
    monkeypatch.setattr(retry_resume_assessment, "_lambda", client)
    return client


def call(monkeypatch, database, resume_id=7):
    monkeypatch.setattr(retry_resume_assessment, "run_query", database)
    response = retry_resume_assessment.handler(candidate_event(ROUTE, resume_id), None)
    return response["statusCode"], json.loads(response["body"])


def retryable_once():
    """A database where the conditional UPDATE matches the first time only, as Postgres would after the reset."""
    state = {"claimed": False}

    def answer(sql, params):
        if sql.startswith("UPDATE"):
            if state["claimed"]:
                return []
            state["claimed"] = True
            return [{"resume_id": params["resume_id"]}]
        return [{"resume_id": params["resume_id"]}]  # the owner check

    return FakeDatabase(answer)


def test_retry_resets_the_row_in_one_conditional_update(monkeypatch, lambda_client):
    database = retryable_once()
    status, body = call(monkeypatch, database)

    assert status == 202
    assert body["status"] == "uploaded"
    sql, params = database.queries[0]
    assert params == {"resume_id": 7, "user_id": USER_ID}
    assert "status = 'uploaded'" in sql
    assert "candidate_id = CAST(:user_id AS uuid)" in sql
    assert "(status = 'failed' AND failure_reason = 'error')" in sql
    assert "status IN ('uploading', 'uploaded', 'reading', 'rating')" in sql
    assert sql.endswith("RETURNING resume_id")


def test_retry_update_restarts_the_stale_clock_and_clears_the_failure(monkeypatch, lambda_client):
    # Without this, the retried row keeps its old timestamp and is reported as timed out on the next check
    database = retryable_once()
    call(monkeypatch, database)

    sql, _ = database.queries[0]
    set_clause = sql.split(" WHERE ")[0]
    assert "status_updated_at = NOW()" in set_clause
    assert "failure_reason = NULL" in set_clause


def test_retry_invokes_the_pipeline_in_the_background(monkeypatch, lambda_client):
    call(monkeypatch, retryable_once())

    assert len(lambda_client.calls) == 1
    invoke = lambda_client.calls[0]
    assert invoke["FunctionName"] == "kerjaready-process-resume"
    assert invoke["InvocationType"] == "Event"
    assert json.loads(invoke["Payload"]) == {"resume_id": 7}


def test_run_that_is_not_retryable_gives_409(monkeypatch, lambda_client):
    # The UPDATE matches nothing (still running, done, or failed with not_pdf), but the resume is theirs
    database = FakeDatabase(lambda sql, params: [] if sql.startswith("UPDATE") else [{"resume_id": 7}])
    status, body = call(monkeypatch, database)

    assert status == 409
    assert "message" in body
    assert lambda_client.calls == []


def test_second_immediate_retry_gives_409_and_starts_one_run(monkeypatch, lambda_client):
    database = retryable_once()
    first, _ = call(monkeypatch, database)
    second, _ = call(monkeypatch, database)

    assert (first, second) == (202, 409)
    assert len(lambda_client.calls) == 1


def test_another_candidates_resume_gives_404(monkeypatch, lambda_client):
    database = FakeDatabase(lambda sql, params: [])
    status, _ = call(monkeypatch, database)

    assert status == 404
    assert lambda_client.calls == []
