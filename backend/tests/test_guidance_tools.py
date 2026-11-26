import json
import sys

import pytest

from conftest import FUNCTIONS_DIR, FakeDatabase

sys.path.insert(0, str(FUNCTIONS_DIR / "run-guidance-agent"))
import guidance_tools  # noqa: E402

RATINGS_ROW = {"a1_rating": 2, "a2_rating": 1, "a3_rating": 3, "b2_rating": 0}
ROLE_ROW = {"title": "AI/ML Engineer", "posting_count": 52}
SKILL_ROWS = [
    {"name": "Machine learning", "demand_share": 0.7885, "match_method": "implied"},
    {"name": "Python", "demand_share": 0.7115, "match_method": "lexical"},
    {"name": "TensorFlow", "demand_share": 0.2692, "match_method": None},
    {"name": "Agile", "demand_share": 0.0962, "match_method": "semantic"},
    {"name": "MLOps", "demand_share": 0.0962},
]
EXPLANATION_ROWS = [
    {"skill_id": 1, "name": "TensorFlow", "demand_share": 0.2692,
     "why_it_matters": "Postings ask for TensorFlow to train models.", "how_to_show": "If you have this skill, name it."},
    {"skill_id": 2, "name": "C#", "demand_share": 0.1346, "why_it_matters": None, "how_to_show": None},
] + [{"skill_id": 10 + i, "name": f"Skill {i}", "demand_share": 0.1, "why_it_matters": "Why.", "how_to_show": "How."}
     for i in range(7)]
SOURCE_ROWS = [
    {"skill_id": 1, "posting_id": 901, "line": "Train models with TensorFlow.", "job_title": "AI Engineer",
     "posted_month": "2026-03"},
    {"skill_id": 1, "posting_id": 902, "line": "TensorFlow or PyTorch.", "job_title": "ML Engineer",
     "posted_month": "2025-11"},
]
# Columns that hold resume text, links or personal details: no tool may read them
PRIVATE_COLUMNS = ["extracted_text", "evidence_excerpt", "file_name", "a1_work_link", "b2_errors", "email", "full_name"]


def database():
    def answer(sql, params):
        if "FROM resume_ratings" in sql:
            return [RATINGS_ROW]
        if "FROM roles ro" in sql:
            return [ROLE_ROW]
        if "FROM role_skill_sources" in sql:
            return SOURCE_ROWS
        if "rq.why_it_matters" in sql:
            return EXPLANATION_ROWS
        if "FROM role_skills" in sql:
            return SKILL_ROWS
        return []
    return FakeDatabase(answer)


@pytest.fixture
def tools(monkeypatch):
    fake = database()
    monkeypatch.setattr(guidance_tools, "run_query", fake)
    get_ratings, get_gap, get_context = guidance_tools.make_tools(9, 4)
    return fake, get_ratings, get_gap, get_context


def test_ratings_use_criterion_names_and_level_labels(tools):
    fake, get_ratings, _, _ = tools
    criteria = json.loads(get_ratings())["criteria"]

    assert [(c["name"], c["level"], c["label"]) for c in criteria] == [
        ("Work Evidence", 2, "Clear"),
        ("Outcome", 1, "Limited"),
        ("Skill in Use", 3, "Strong"),
        ("Language Quality", 0, "Hard to read"),
    ]
    assert all(c["out_of"] == 3 for c in criteria)
    assert fake.queries[0][1] == {"resume_id": 9}


def test_ratings_give_the_rubrics_next_level_wording(tools):
    _, get_ratings, _, _ = tools
    next_level = {c["name"]: c["next_level"] for c in json.loads(get_ratings())["criteria"]}

    assert next_level["Work Evidence"].startswith("A link to the work itself")
    assert next_level["Outcome"].startswith("A concrete result in more than half")
    assert next_level["Skill in Use"] is None
    assert next_level["Language Quality"] is None


def test_skill_gap_gives_names_match_types_and_posting_counts(tools):
    fake, _, get_gap, _ = tools
    gap = json.loads(get_gap())

    assert gap["target_role"] == "AI/ML Engineer" and gap["role_postings"] == 52
    assert gap["evidenced"] == [
        {"skill": "Machine learning", "postings": 41, "share_percent": 79, "match": "shown through a related tool"},
        {"skill": "Python", "postings": 37, "share_percent": 71, "match": "named in the resume"},
        {"skill": "Agile", "postings": 5, "share_percent": 10, "match": "similar wording"},
    ]
    assert gap["not_evidenced"] == [
        {"skill": "TensorFlow", "postings": 14, "share_percent": 27},
        {"skill": "MLOps", "postings": 5, "share_percent": 10},
    ]
    assert fake.queries[0][1] == {"role_id": 4}
    assert fake.queries[1][1] == {"resume_id": 9, "role_id": 4}


def test_tools_are_bound_to_the_run_and_take_no_ids(tools):
    _, get_ratings, get_gap, get_context = tools
    for tool in (get_ratings, get_gap):
        assert tool.tool_spec["inputSchema"]["json"].get("properties", {}) == {}
    # Market context takes only skill names: the role comes from the run
    assert list(get_context.tool_spec["inputSchema"]["json"]["properties"]) == ["skills"]


def test_tool_descriptions_say_not_evidenced_is_not_lacking(tools):
    _, get_ratings, get_gap, _ = tools
    def description(tool):
        return " ".join(tool.tool_spec["description"].split())

    assert "not that the candidate lacks it" in description(get_ratings)
    assert "not one the candidate lacks" in description(get_gap)


def test_market_context_gives_explanations_and_posting_lines_for_the_roles_skills(tools):
    fake, _, _, get_context = tools
    context = json.loads(get_context(["tensorflow", "C#", "Kubernetes", "TensorFlow"]))

    tensorflow, csharp = context["skills"]
    assert tensorflow == {
        "skill": "TensorFlow", "postings": 14, "role_postings": 52,
        "why_it_matters": "Postings ask for TensorFlow to train models.", "how_to_show": "If you have this skill, name it.",
        "posting_lines": [
            {"posting_id": 901, "line": "Train models with TensorFlow.", "job_title": "AI Engineer", "posted": "2026-03"},
            {"posting_id": 902, "line": "TensorFlow or PyTorch.", "job_title": "ML Engineer", "posted": "2025-11"},
        ],
    }
    # A skill with no explanation yet still comes back, with nulls and no lines
    assert csharp["why_it_matters"] is None and csharp["posting_lines"] == []
    # Names outside the role profile are reported, not looked up
    assert context["not_in_role_profile"] == ["Kubernetes"]
    assert all(params == {"role_id": 4} for _, params in fake.queries)


def test_market_context_looks_up_at_most_six_skills(tools):
    _, _, _, get_context = tools
    context = json.loads(get_context([f"Skill {i}" for i in range(7)]))

    assert [s["skill"] for s in context["skills"]] == [f"Skill {i}" for i in range(6)]
    assert context["note"] == "Only the first 6 skills were looked up; ask again for the rest."


def test_no_tool_reads_resume_text_links_or_personal_details():
    queries = (guidance_tools.RATINGS + guidance_tools.ROLE + guidance_tools.SKILLS + guidance_tools.EXPLANATIONS
               + guidance_tools.SOURCES)
    for column in PRIVATE_COLUMNS:
        assert column not in queries, column


def test_missing_data_is_reported_not_raised(monkeypatch):
    monkeypatch.setattr(guidance_tools, "run_query", FakeDatabase())
    get_ratings, get_gap, get_context = guidance_tools.make_tools(9, 4)
    assert json.loads(get_ratings()) == {"error": "This resume has no assessment ratings."}
    assert json.loads(get_gap()) == {"error": "The target role was not found."}
    assert json.loads(get_context(["Python"])) == {"error": "The target role was not found."}