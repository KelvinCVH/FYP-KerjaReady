import json

from conftest import USER_ID, FakeDatabase, load_function

list_resumes = load_function("list-resumes")
ROUTE = "GET /candidate/resumes"


def call(monkeypatch, database, groups="[candidate]"):
    monkeypatch.setattr(list_resumes, "run_query", database)
    event = {
        "routeKey": ROUTE,
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": USER_ID, "cognito:groups": groups}}}},
    }
    response = list_resumes.handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def test_lists_only_the_candidates_own_resumes_newest_first_without_uploading_rows(monkeypatch):
    database = FakeDatabase()
    status, body = call(monkeypatch, database)

    assert status == 200
    assert body == {"resumes": []}
    sql, params = database.queries[0]
    assert params == {"user_id": USER_ID}
    assert "WHERE candidate_id = CAST(:user_id AS uuid)" in sql
    assert "status <> 'uploading'" in sql
    assert "ORDER BY resume_id DESC LIMIT 50" in sql


def test_rows_carry_the_reported_status_and_failure_reason(monkeypatch):
    rows = [
        {"resume_id": 9, "file_name": "new.pdf", "uploaded_at": "2026-11-17T10:00:00Z", "status": "rating", "failure_reason": None},
        {"resume_id": 4, "file_name": "scan.pdf", "uploaded_at": "2026-11-10T10:00:00Z", "status": "failed", "failure_reason": "no_text"},
    ]
    database = FakeDatabase(lambda sql, params: rows)
    _, body = call(monkeypatch, database)

    assert [row["resume_id"] for row in body["resumes"]] == [9, 4]
    assert body["resumes"][1] == rows[1]
    sql, _ = database.queries[0]
    assert "THEN 'timed_out'" in sql  # stalled runs are reported as timed_out, as on the status route


def test_recruiter_cannot_list_candidate_resumes(monkeypatch):
    database = FakeDatabase()
    status, _ = call(monkeypatch, database, groups="[recruiter]")

    assert status == 403
    assert database.queries == []