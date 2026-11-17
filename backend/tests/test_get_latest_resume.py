import json

import pytest
from conftest import USER_ID, FakeDatabase, candidate_event, load_function

get_latest_resume = load_function("get-latest-resume")
LATEST = "GET /candidate/resumes/latest"
BY_ID = "GET /candidate/resumes/{resume_id}"

DONE_ROW = {
    "resume_id": 7, "file_name": "cv.pdf", "s3_key": "resumes/u/7.pdf", "status": "done", "failure_reason": None,
    "uploaded_at": "2026-11-10T10:00:00Z", "a1_rating": 2, "a2_rating": 1, "a3_rating": 2, "b2_rating": 3,
    "a1_work_link": None, "b2_errors": "[]", "model_version": "kerjaready-rating-model-20261111-114855",
    "rated_at": "2026-11-10T10:01:00Z",
}


@pytest.fixture(autouse=True)
def no_s3(monkeypatch):
    monkeypatch.setattr(get_latest_resume, "view_url", lambda s3_key: f"https://example.test/{s3_key}")


def call(monkeypatch, database, event):
    monkeypatch.setattr(get_latest_resume, "run_query", database)
    response = get_latest_resume.handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def latest_event():
    event = candidate_event(LATEST, 0)
    event.pop("pathParameters")
    return event


def test_latest_with_no_resume_returns_null(monkeypatch):
    status, body = call(monkeypatch, FakeDatabase(), latest_event())

    assert status == 200
    assert body == {"resume": None}


def test_latest_does_not_filter_by_resume_id(monkeypatch):
    database = FakeDatabase(lambda sql, params: [DONE_ROW])
    status, body = call(monkeypatch, database, latest_event())

    assert status == 200
    assert body["resume"]["ratings"]["a1"] == 2
    sql, params = database.queries[0]
    assert ":resume_id" not in sql
    assert params == {"user_id": USER_ID}


def test_by_id_returns_the_candidates_own_resume(monkeypatch):
    database = FakeDatabase(lambda sql, params: [DONE_ROW])
    status, body = call(monkeypatch, database, candidate_event(BY_ID, 7))

    assert status == 200
    assert body["resume"]["resume_id"] == 7
    assert body["resume"]["view_url"] == "https://example.test/resumes/u/7.pdf"
    sql, params = database.queries[0]
    assert "r.candidate_id = CAST(:user_id AS uuid)" in sql
    assert "AND r.resume_id = :resume_id" in sql
    assert params == {"user_id": USER_ID, "resume_id": 7}


def test_by_id_for_another_candidates_resume_gives_404(monkeypatch):
    # The query is filtered by owner, so another candidate's resume returns no row
    status, body = call(monkeypatch, FakeDatabase(), candidate_event(BY_ID, 99))

    assert status == 404
    assert "message" in body


def test_by_id_that_is_not_a_number_gives_404_without_a_query(monkeypatch):
    database = FakeDatabase()
    status, _ = call(monkeypatch, database, candidate_event(BY_ID, "abc"))

    assert status == 404
    assert database.queries == []