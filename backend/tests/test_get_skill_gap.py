import json

from conftest import USER_ID, FakeDatabase, candidate_event, load_function

get_skill_gap = load_function("get-skill-gap")
ROUTE = "GET /candidate/resumes/{resume_id}/skill-gap"

POSTING_COUNT = 52
ROLE_ROW = {"status": "done", "role_id": 4, "title": "Data Analyst", "posting_count": POSTING_COUNT,
            "first_posted": "2024-02-01", "last_posted": "2026-10-28"}
# As the database orders them, demand share highest first. Shares are stored to 4 dp, as the pipeline writes them:
# 41/52 = 0.7885, 14/52 = 0.2692, 9/52 = 0.1731, 7/52 = 0.1346
TABLEAU_WHY = "Data Analyst postings ask for Tableau to build dashboards. It often comes with SQL."
TABLEAU_HOW = "If you have this skill, name Tableau in a project line with the dashboard you built."
SKILL_ROWS = [
    {"skill_id": 1, "name": "SQL", "demand_share": 0.7885, "evidence": "Skills: Python, SQL", "match_method": "lexical",
     "why_it_matters": "SQL explanation.", "how_to_show": "If you have this skill, show SQL."},
    {"skill_id": 2, "name": "Tableau", "demand_share": 0.2692, "why_it_matters": TABLEAU_WHY, "how_to_show": TABLEAU_HOW},
    {"skill_id": 3, "name": "Data visualisation", "demand_share": 0.1731,
     "evidence": "Built Power BI dashboards for sales", "match_method": "semantic"},
    # Not explained yet: the knowledge base load has not added its explanation
    {"skill_id": 4, "name": "Statistics", "demand_share": 0.1346, "why_it_matters": None, "how_to_show": None},
]
# As the database orders them: by skill, newest posting first
SOURCE_ROWS = [
    {"skill_id": 1, "posting_id": 900, "line": "Write SQL queries.", "job_title": "Data Analyst",
     "posted_date": "2026-01-10"},
    {"skill_id": 2, "posting_id": 901, "line": "Build Tableau dashboards for sales.", "job_title": "Junior Data Analyst",
     "posted_date": "2026-03-02"},
    {"skill_id": 2, "posting_id": 902, "line": "Tableau or Power BI reporting.", "job_title": "Data Analyst Intern",
     "posted_date": "2025-11-20"},
]


def database_with(resume_row, skill_rows=SKILL_ROWS, source_rows=SOURCE_ROWS):
    def answer(sql, params):
        if "FROM resumes r" in sql:
            return [resume_row] if resume_row else []
        if "FROM role_skill_sources" in sql:
            return source_rows
        return skill_rows
    return FakeDatabase(answer)


def call(monkeypatch, database, resume_id=7, route=ROUTE):
    monkeypatch.setattr(get_skill_gap, "run_query", database)
    response = get_skill_gap.handler(candidate_event(route, resume_id), None)
    return response["statusCode"], json.loads(response["body"])


def test_skills_split_into_evidenced_and_not_evidenced_in_demand_order(monkeypatch):
    status, body = call(monkeypatch, database_with(ROLE_ROW))

    assert status == 200
    assert body["target_role"] == {"role_id": 4, "title": "Data Analyst", "posting_count": POSTING_COUNT,
                                   "first_posted": "2024-02-01", "last_posted": "2026-10-28"}
    assert body["evidenced"] == [
        {"skill_id": 1, "name": "SQL", "demand_share": 0.7885, "postings": 41,
         "evidence": "Skills: Python, SQL", "match_method": "lexical"},
        {"skill_id": 3, "name": "Data visualisation", "demand_share": 0.1731, "postings": 9,
         "evidence": "Built Power BI dashboards for sales", "match_method": "semantic"},
    ]
    assert body["not_evidenced"] == [
        {"skill_id": 2, "name": "Tableau", "demand_share": 0.2692, "postings": 14,
         "why_it_matters": TABLEAU_WHY, "how_to_show": TABLEAU_HOW,
         "sources": [
             {"posting_id": 901, "line": "Build Tableau dashboards for sales.", "job_title": "Junior Data Analyst",
              "posted_date": "2026-03-02"},
             {"posting_id": 902, "line": "Tableau or Power BI reporting.", "job_title": "Data Analyst Intern",
              "posted_date": "2025-11-20"},
         ]},
        {"skill_id": 4, "name": "Statistics", "demand_share": 0.1346, "postings": 7,
         "why_it_matters": None, "how_to_show": None, "sources": []},
    ]


def test_postings_give_back_the_exact_count_behind_each_4dp_share(monkeypatch):
    # Every possible count for a 52-posting role, with its share rounded to 4 dp as the pipeline stores it
    rows = [{"skill_id": count, "name": f"Skill {count}", "demand_share": round(count / POSTING_COUNT, 4)}
            for count in range(POSTING_COUNT, -1, -1)]
    _, body = call(monkeypatch, database_with(ROLE_ROW, rows))

    assert [skill["postings"] for skill in body["not_evidenced"]] == list(range(POSTING_COUNT, -1, -1))
    assert all(isinstance(skill["postings"], int) for skill in body["not_evidenced"])


def test_every_role_skill_appears_in_exactly_one_group(monkeypatch):
    _, body = call(monkeypatch, database_with(ROLE_ROW))

    names = [skill["name"] for skill in body["evidenced"] + body["not_evidenced"]]
    assert sorted(names) == sorted(row["name"] for row in SKILL_ROWS)


def test_queries_are_limited_to_the_candidate_their_resume_and_their_role(monkeypatch):
    database = database_with(ROLE_ROW)
    call(monkeypatch, database)

    (resume_sql, resume_params), (skills_sql, skills_params), (sources_sql, sources_params) = database.queries
    assert "r.candidate_id = CAST(:user_id AS uuid)" in resume_sql
    assert resume_params == {"resume_id": 7, "user_id": USER_ID}
    assert "LEFT JOIN resume_skills" in skills_sql and "ORDER BY rq.demand_share DESC" in skills_sql
    assert skills_params == {"resume_id": 7, "role_id": 4}
    assert "WHERE src.role_id = :role_id" in sources_sql and "jp.posted_date DESC" in sources_sql
    assert sources_params == {"role_id": 4}


def test_evidenced_skills_carry_no_explanation(monkeypatch):
    _, body = call(monkeypatch, database_with(ROLE_ROW))

    for skill in body["evidenced"]:
        assert not {"why_it_matters", "how_to_show", "sources"} & set(skill)


def test_no_source_query_when_every_skill_is_evidenced(monkeypatch):
    rows = [row for row in SKILL_ROWS if row.get("evidence")]
    database = database_with(ROLE_ROW, rows)
    _, body = call(monkeypatch, database)

    assert body["not_evidenced"] == []
    assert len(database.queries) == 2


def test_posting_date_range_is_the_first_and_last_posted_date_of_the_role(monkeypatch):
    database = database_with(ROLE_ROW)
    call(monkeypatch, database)

    resume_sql, _ = database.queries[0]
    assert "to_char(min(jp.posted_date), 'YYYY-MM-DD') AS first_posted" in resume_sql
    assert "to_char(max(jp.posted_date), 'YYYY-MM-DD') AS last_posted" in resume_sql
    assert "WHERE jp.role_id = u.target_role_id" in resume_sql


def test_role_without_postings_gives_null_dates(monkeypatch):
    database = database_with({**ROLE_ROW, "posting_count": 0, "first_posted": None, "last_posted": None}, [])
    status, body = call(monkeypatch, database)

    assert status == 200
    assert body["target_role"] == {"role_id": 4, "title": "Data Analyst", "posting_count": 0,
                                   "first_posted": None, "last_posted": None}
    assert body["evidenced"] == [] and body["not_evidenced"] == []


def test_no_target_role_gives_empty_groups_without_a_skill_query(monkeypatch):
    database = database_with({**ROLE_ROW, "role_id": None, "title": None, "posting_count": 0})
    status, body = call(monkeypatch, database)

    assert status == 200
    assert body == {"resume_id": 7, "target_role": None, "evidenced": [], "not_evidenced": []}
    assert len(database.queries) == 1


def test_resume_still_being_assessed_gives_409(monkeypatch):
    database = database_with({**ROLE_ROW, "status": "rating"})
    status, _ = call(monkeypatch, database)

    assert status == 409
    assert len(database.queries) == 1


def test_missing_or_another_candidates_resume_gives_404(monkeypatch):
    status, _ = call(monkeypatch, database_with(None))
    assert status == 404


def test_resume_still_uploading_gives_404(monkeypatch):
    status, _ = call(monkeypatch, database_with({**ROLE_ROW, "status": "uploading"}))
    assert status == 404


def test_resume_id_that_is_not_a_number_gives_404_without_a_query(monkeypatch):
    database = database_with(ROLE_ROW)
    status, _ = call(monkeypatch, database, resume_id="abc")

    assert status == 404
    assert database.queries == []