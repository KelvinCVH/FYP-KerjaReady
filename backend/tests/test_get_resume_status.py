import json

from conftest import USER_ID, FakeDatabase, candidate_event, load_function
from kerjaready_shared.resume_status import STALE_AFTER_SECONDS

get_resume_status = load_function("get-resume-status")
ROUTE = "GET /candidate/resumes/{resume_id}/status"


def call(monkeypatch, database, resume_id=7):
    monkeypatch.setattr(get_resume_status, "run_query", database)
    response = get_resume_status.handler(candidate_event(ROUTE, resume_id), None)
    return response["statusCode"], json.loads(response["body"])


def test_another_candidates_resume_gives_404(monkeypatch):
    # The query is filtered by owner, so another candidate's resume returns no row
    database = FakeDatabase(lambda sql, params: [])
    status, body = call(monkeypatch, database)

    assert status == 404
    assert "message" in body
    sql, params = database.queries[0]
    assert "candidate_id = CAST(:user_id AS uuid)" in sql
    assert params == {"resume_id": 7, "user_id": USER_ID}


def test_resume_id_that_is_not_a_number_gives_404_without_a_query(monkeypatch):
    database = FakeDatabase()
    status, _ = call(monkeypatch, database, resume_id="abc")

    assert status == 404
    assert database.queries == []


def test_timed_out_is_worked_out_in_sql_by_the_database_clock(monkeypatch):
    database = FakeDatabase(lambda sql, params: [{"status": "timed_out", "failure_reason": None}])
    status, body = call(monkeypatch, database)

    assert status == 200
    assert body == {"status": "timed_out", "failure_reason": None}
    sql, _ = database.queries[0]
    assert f"status_updated_at < NOW() - make_interval(secs => {STALE_AFTER_SECONDS})" in sql
    assert "THEN 'timed_out'" in sql
    # Every running status can stall, including a file that never reached S3
    assert "'uploading', 'uploaded', 'reading', 'rating'" in sql


def test_failed_status_returns_its_code(monkeypatch):
    database = FakeDatabase(lambda sql, params: [{"status": "failed", "failure_reason": "no_text"}])
    status, body = call(monkeypatch, database)

    assert status == 200
    assert body == {"status": "failed", "failure_reason": "no_text"}
