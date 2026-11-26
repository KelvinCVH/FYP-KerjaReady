import json

import pytest

from conftest import USER_ID, FakeDatabase, load_function

get_roadmap = load_function("get-roadmap")
ROUTE = "GET /candidate/roadmap"

CONTEXT_ROW = {"role_id": 4, "title": "AI/ML Engineer", "posting_count": 52,
               "resume_id": 331, "file_name": "Resume_v3.pdf", "assessed_at": "2026-11-17T08:12:00Z"}
RUN_ROW = {"run_id": 200, "status": "done", "created_at": "2026-11-26T01:10:00Z",
           "finished_at": "2026-11-26T01:10:22Z"}
RATINGS_ROW = {"a1_rating": 2, "a2_rating": 1, "a3_rating": 2, "b2_rating": 3}
# 14/52 = 0.2692, 8/52 = 0.1538, 7/52 = 0.1346
PROFILE_ROWS = [
    {"name": "TensorFlow", "demand_share": 0.2692, "why_it_matters": "Postings ask for TensorFlow to train models."},
    {"name": "Microsoft Azure", "demand_share": 0.1538, "why_it_matters": None},
    {"name": "Computer vision", "demand_share": 0.1346, "why_it_matters": "Postings ask for computer vision."},
    {"name": "Data analysis", "demand_share": 0.1346, "why_it_matters": "Postings ask for data analysis."},
    {"name": "Data science", "demand_share": 0.1346, "why_it_matters": "Postings ask for data science."},
]


def milestone(skill, learning_order=None):
    return {"skill": skill, "prerequisites": "Python.", "learning_order": learning_order,
            "objectives": ["One", "Two", "Three"], "key_topics": ["A", "B", "C", "D"],
            "practice_project": {"title": "T", "description": "D", "deliverable": "R"},
            "ready_when": ["One", "Two"], "resume_line": "Built [what].", "search_terms": [f"{skill} course"],
            "source_posting_ids": [901]}


def step(criterion):
    return {"criterion": criterion, "how_to_improve": "How.", "example_line": "Built [what].", "linked_skills": []}


OUTPUT = {
    "resume_steps": [step("Outcome"), step("Skill in Use")],
    "skill_milestones": [
        milestone("TensorFlow"),
        milestone("Microsoft Azure", "Learn this after TensorFlow, because you can deploy that model."),
        milestone("Computer vision", "Learn this after TensorFlow, because it trains the model."),
        milestone("Data science", "Learn this after Data analysis and TensorFlow, because it combines both."),
        milestone("Data analysis", "Learn this after PyTorch, because it compares."),
    ],
}


def database_with(context=CONTEXT_ROW, run=RUN_ROW, output=OUTPUT, ratings=RATINGS_ROW, profile=PROFILE_ROWS):
    def answer(sql, params):
        if "FROM users u" in sql:
            return [context] if context else []
        if "FROM agent_runs" in sql:
            return [{**run, "output": json.dumps(output) if output else None}] if run else []
        if "FROM resume_ratings" in sql:
            return [ratings] if ratings else []
        if "FROM role_skills" in sql:
            return profile
        return []
    return FakeDatabase(answer)


def call(monkeypatch, database):
    monkeypatch.setattr(get_roadmap.roadmap_runs, "run_query", database)
    monkeypatch.setattr(get_roadmap, "run_query", database)
    claims = {"sub": USER_ID, "cognito:groups": "[candidate]"}
    response = get_roadmap.handler({"routeKey": ROUTE, "requestContext": {"authorizer": {"jwt": {"claims": claims}}}},
                                   None)
    return response["statusCode"], json.loads(response["body"])


def test_a_finished_roadmap_comes_back_with_what_the_database_adds(monkeypatch):
    database = database_with()
    status, body = call(monkeypatch, database)

    assert status == 200
    assert body["resume"] == {"resume_id": 331, "file_name": "Resume_v3.pdf", "assessed_at": "2026-11-17T08:12:00Z"}
    assert body["target_role"] == {"role_id": 4, "title": "AI/ML Engineer", "posting_count": 52}
    assert body["run"] == {"run_id": 200, "status": "done", "created_at": "2026-11-26T01:10:00Z",
                           "finished_at": "2026-11-26T01:10:22Z"}
    assert database.queries[0][1] == {"user_id": USER_ID}
    assert database.queries[1][1] == {"resume_id": 331, "role_id": 4}


def test_resume_steps_get_their_level_and_next_level_labels(monkeypatch):
    _, body = call(monkeypatch, database_with())
    outcome, skill_in_use = body["roadmap"]["resume_steps"]

    assert (outcome["level"], outcome["level_label"], outcome["next_label"]) == (1, "Limited", "Clear")
    assert (skill_in_use["level"], skill_in_use["level_label"], skill_in_use["next_label"]) == (2, "Clear", "Strong")
    assert outcome["how_to_improve"] == "How."


@pytest.mark.parametrize("criterion", ["Language Quality", "Unknown criterion"])
def test_a_step_at_the_top_level_or_outside_the_rubric_is_left_out(monkeypatch, criterion):
    output = {**OUTPUT, "resume_steps": [step(criterion), step("Outcome")]}
    _, body = call(monkeypatch, database_with(output=output))
    assert [s["criterion"] for s in body["roadmap"]["resume_steps"]] == ["Outcome"]


def test_milestones_get_posting_counts_and_stored_explanations(monkeypatch):
    _, body = call(monkeypatch, database_with())
    milestones = {m["skill"]: m for m in body["roadmap"]["skill_milestones"]}

    assert [m["skill"] for m in body["roadmap"]["skill_milestones"]] == [
        "TensorFlow", "Microsoft Azure", "Computer vision", "Data science", "Data analysis"]
    assert (milestones["TensorFlow"]["postings"], milestones["TensorFlow"]["role_postings"]) == (14, 52)
    assert milestones["Microsoft Azure"]["postings"] == 8
    assert milestones["TensorFlow"]["why_it_matters"] == "Postings ask for TensorFlow to train models."
    assert milestones["Microsoft Azure"]["why_it_matters"] is None
    assert milestones["TensorFlow"]["key_topics"] == ["A", "B", "C", "D"]


def test_learn_after_names_only_other_milestones(monkeypatch):
    _, body = call(monkeypatch, database_with())
    learn_after = {m["skill"]: m["learn_after"] for m in body["roadmap"]["skill_milestones"]}

    assert learn_after == {
        "TensorFlow": None,
        "Microsoft Azure": "TensorFlow",
        "Computer vision": "TensorFlow",
        "Data science": "TensorFlow and Data analysis",
        "Data analysis": None,
    }


def test_a_skill_no_longer_in_the_role_profile_shows_no_postings(monkeypatch):
    _, body = call(monkeypatch, database_with(profile=PROFILE_ROWS[1:]))
    tensorflow = body["roadmap"]["skill_milestones"][0]
    assert tensorflow["postings"] == 0 and tensorflow["why_it_matters"] is None


@pytest.mark.parametrize("status", ["running", "failed"])
def test_an_unfinished_run_comes_back_without_a_roadmap(monkeypatch, status):
    database = database_with(run={**RUN_ROW, "status": status, "finished_at": None}, output=None)
    _, body = call(monkeypatch, database)

    assert body["run"]["status"] == status and body["roadmap"] is None
    assert len(database.queries) == 2


def test_a_stuck_run_is_reported_as_failed_by_the_database_clock(monkeypatch):
    database = database_with()
    call(monkeypatch, database)
    run_sql = database.queries[1][0]
    assert "CASE WHEN (status = 'running' AND created_at < NOW() - make_interval(secs => 360)) THEN 'failed'" in run_sql
    assert "output_type = 'roadmap'" in run_sql


def test_no_run_yet(monkeypatch):
    _, body = call(monkeypatch, database_with(run=None))
    assert body["run"] is None and body["roadmap"] is None


def test_no_assessed_resume(monkeypatch):
    context = {**CONTEXT_ROW, "resume_id": None, "file_name": None, "assessed_at": None}
    database = database_with(context=context)
    _, body = call(monkeypatch, database)

    assert body["resume"] is None and body["run"] is None and body["roadmap"] is None
    assert body["target_role"]["title"] == "AI/ML Engineer"
    assert len(database.queries) == 1


def test_no_target_role(monkeypatch):
    context = {**CONTEXT_ROW, "role_id": None, "title": None, "posting_count": 0}
    database = database_with(context=context)
    _, body = call(monkeypatch, database)

    assert body["target_role"] is None and body["resume"]["resume_id"] == 331 and body["run"] is None
    assert len(database.queries) == 1


def test_the_latest_assessed_resume_skips_ones_still_being_assessed(monkeypatch):
    database = database_with()
    call(monkeypatch, database)
    context_sql = database.queries[0][0]
    assert "r.status = 'done'" in context_sql and "ORDER BY r.resume_id DESC" in context_sql


def test_a_recruiter_cannot_read_a_roadmap(monkeypatch):
    claims = {"sub": USER_ID, "cognito:groups": "[recruiter]"}
    response = get_roadmap.handler({"routeKey": ROUTE, "requestContext": {"authorizer": {"jwt": {"claims": claims}}}},
                                   None)
    assert response["statusCode"] == 403