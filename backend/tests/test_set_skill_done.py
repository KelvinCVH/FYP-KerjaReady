import json

import pytest

from conftest import USER_ID, FakeDatabase, load_function

set_skill_done = load_function("set-skill-done")
PUT = "PUT /candidate/done-skills/{skill_id}"
DELETE = "DELETE /candidate/done-skills/{skill_id}"


def database_with(skill_exists=True):
    def answer(sql, params):
        if sql.startswith("SELECT skill_id FROM skills"):
            return [{"skill_id": params["skill_id"]}] if skill_exists else []
        return []
    return FakeDatabase(answer)


def event(route_key, path_parameters, group="candidate"):
    claims = {"sub": USER_ID, "cognito:groups": f"[{group}]"}
    return {"routeKey": route_key, "pathParameters": path_parameters,
            "requestContext": {"authorizer": {"jwt": {"claims": claims}}}}


def call(monkeypatch, database, route_key, skill_id="12", group="candidate"):
    monkeypatch.setattr(set_skill_done, "run_query", database)
    path_parameters = None if skill_id is None else {"skill_id": skill_id}
    response = set_skill_done.handler(event(route_key, path_parameters, group), None)
    return response["statusCode"], json.loads(response["body"])


def writes(database):
    return [(sql, params) for sql, params in database.queries if not sql.startswith("SELECT")]


def test_put_marks_the_skill_done_for_the_candidate(monkeypatch):
    database = database_with()
    status, body = call(monkeypatch, database, PUT)

    assert status == 200 and body == {"skill_id": 12, "done": True}
    assert database.queries[0] == ("SELECT skill_id FROM skills WHERE skill_id = :skill_id", {"skill_id": 12})
    [(sql, params)] = writes(database)
    assert sql.strip().startswith("INSERT INTO done_skills (candidate_id, skill_id)")
    assert "ON CONFLICT DO NOTHING" in sql
    assert params == {"user_id": USER_ID, "skill_id": 12}


def test_put_twice_gives_the_same_answer(monkeypatch):
    database = database_with()
    first = call(monkeypatch, database, PUT)
    second = call(monkeypatch, database, PUT)

    assert first == second == (200, {"skill_id": 12, "done": True})
    assert len(writes(database)) == 2


def test_delete_undoes_the_mark_for_the_candidate(monkeypatch):
    database = database_with()
    status, body = call(monkeypatch, database, DELETE)

    assert status == 200 and body == {"skill_id": 12, "done": False}
    [(sql, params)] = writes(database)
    assert sql.strip() == "DELETE FROM done_skills WHERE candidate_id = CAST(:user_id AS uuid) AND skill_id = :skill_id"
    assert params == {"user_id": USER_ID, "skill_id": 12}


def test_delete_of_a_skill_that_is_not_done_still_succeeds(monkeypatch):
    # The fake DELETE removes no rows, as when the skill was never marked
    database = database_with()
    first = call(monkeypatch, database, DELETE)
    second = call(monkeypatch, database, DELETE)
    assert first == second == (200, {"skill_id": 12, "done": False})


@pytest.mark.parametrize("route_key", [PUT, DELETE])
def test_an_unknown_skill_gives_404_without_a_write(monkeypatch, route_key):
    database = database_with(skill_exists=False)
    status, body = call(monkeypatch, database, route_key, skill_id="999999")

    assert status == 404 and body == {"message": "We couldn't find this skill."}
    assert len(database.queries) == 1 and writes(database) == []


@pytest.mark.parametrize("skill_id", ["abc", "0", "-3", "1.5", "", "²", "007", "1" * 20, None])
@pytest.mark.parametrize("route_key", [PUT, DELETE])
def test_a_skill_id_that_is_not_a_positive_whole_number_gives_400_without_a_query(monkeypatch, route_key, skill_id):
    database = database_with()
    status, body = call(monkeypatch, database, route_key, skill_id=skill_id)

    assert status == 400 and body == {"message": "Choose a skill from your roadmap."}
    assert database.queries == []


def test_the_largest_skill_id_that_fits_is_accepted(monkeypatch):
    status, body = call(monkeypatch, database_with(), PUT, skill_id="9" * 18)
    assert status == 200 and body["skill_id"] == int("9" * 18)


@pytest.mark.parametrize("route_key", [PUT, DELETE])
def test_a_recruiter_cannot_mark_skills(monkeypatch, route_key):
    database = database_with()
    status, _ = call(monkeypatch, database, route_key, group="recruiter")
    assert status == 403 and database.queries == []


def test_another_method_gives_405_without_a_query(monkeypatch):
    database = database_with()
    status, _ = call(monkeypatch, database, "POST /candidate/done-skills/{skill_id}")
    assert status == 405 and database.queries == []
