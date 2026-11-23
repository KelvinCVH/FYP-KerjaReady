"""Tests for resume skill matching. Run: python -m pytest backend/functions/assess-resume"""

from pathlib import Path

import numpy as np
import pytest

import match_resume_skills as matching
from match_resume_skills import evidence_text, match_resume_skills, semantic_lines
from skill_matching import find_skills, load_implications, load_vocabulary

PIPELINE_DIR = Path(__file__).resolve().parents[3] / "knowledge-base-pipeline"
VOCABULARY_CSV = PIPELINE_DIR / "skill_vocabulary.csv"
IMPLICATIONS_CSV = PIPELINE_DIR / "skill_implications.csv"

RESUME = """Kelvin Chin
Bachelor of Computer Science (Data Science)
Skills: Python, SQL, Docker
Built Power BI dashboards that show monthly sales by region for the finance team
Led R&D on a churn model with the data team
"""


class FakeEmbedder:
    """Three skills in a 3-d space. A line points at a skill when it contains the skill's keyword."""

    skill_names = ["Python", "Data visualisation", "Agile"]
    skill_vectors = np.eye(3, dtype=np.float32)
    keywords = ["python", "dashboards", "sprints"]

    def embed(self, texts):
        vectors = np.array([[1.0 if k in t.lower() else 0.05 for k in self.keywords] for t in texts], dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


@pytest.fixture(scope="module")
def vocabulary():
    return load_vocabulary(VOCABULARY_CSV)


@pytest.fixture(scope="module")
def implications(vocabulary):
    return load_implications(IMPLICATIONS_CSV, [skill for skill, _ in vocabulary])


@pytest.fixture
def no_semantic(monkeypatch):
    monkeypatch.setattr(matching, "SEMANTIC_THRESHOLD", None)


def test_vocabulary_loads_every_skill_without_pandas(vocabulary):
    assert len(vocabulary) == 281
    assert vocabulary[0][0] == "Python" and vocabulary[0][1]


def test_rule_based_match_keeps_the_existing_behaviour(vocabulary):
    found = find_skills(RESUME, vocabulary)
    assert {"Python", "SQL", "Docker"} <= set(found)
    assert found["Python"] == "Skills: Python, SQL, Docker"
    assert "R" not in found  # "R&D" is blocked
    assert "Data science" not in found  # field of study on a degree line


def test_semantic_lines_skip_short_duplicate_and_degree_lines():
    text = "Skills: Python, SQL\nBachelor of Computer Science (Data Science)\n" \
           "Built dashboards for   the sales team\nBuilt dashboards for the sales team\n"
    assert semantic_lines(text) == ["Built dashboards for the sales team"]


def test_semantic_match_is_off_until_the_threshold_is_set(vocabulary, monkeypatch):
    monkeypatch.setattr(matching, "SEMANTIC_THRESHOLD", None)
    matches = match_resume_skills(RESUME, vocabulary, FakeEmbedder(), {})
    assert matches and all(match["method"] == "lexical" for match in matches)


def test_semantic_match_adds_only_skills_the_rules_did_not_find(vocabulary, monkeypatch):
    monkeypatch.setattr(matching, "SEMANTIC_SCORE", "raw")
    monkeypatch.setattr(matching, "SEMANTIC_THRESHOLD", 0.9)
    matches = match_resume_skills(RESUME, vocabulary, FakeEmbedder(), {})
    semantic = [match for match in matches if match["method"] == "semantic"]
    assert semantic == [{
        "skill": "Data visualisation",
        "evidence": "Built Power BI dashboards that show monthly sales by region for the finance team",
        "method": "semantic",
    }]
    assert len({match["skill"] for match in matches}) == len(matches)  # Python stays a rule-based match only


def test_relative_score_is_how_far_a_skill_stands_out_on_its_line():
    scores = matching.line_skill_scores(["Built dashboards for the sales team"], FakeEmbedder())
    assert scores["relative"][0].argmax() == 1
    assert np.isclose(scores["relative"][0].mean(), 0.0, atol=1e-6)


@pytest.mark.parametrize("line, shown", [
    ("ò Involved in UI/UX design for the client.", "Involved in UI/UX design for the client."),
    ("•  Built Power BI dashboards", "Built Power BI dashboards"),
    ("- Wrote unit tests in pytest", "Wrote unit tests in pytest"),
    ("$2M budget managed for the rollout", "$2M budget managed for the rollout"),
    ("C++ developer for embedded firmware", "C++ developer for embedded firmware"),
    ("(Python) data cleaning scripts", "(Python) data cleaning scripts"),
])
def test_evidence_lines_lose_only_a_leading_bullet(line, shown):
    assert evidence_text(line) == shown

def test_the_implied_skill_list_loads_and_only_names_vocabulary_skills(vocabulary, implications):
    names = {skill for skill, _ in vocabulary}
    pairs = [(skill, broader) for skill, broaders in implications.items() for broader in broaders]
    assert len(pairs) == 206 and len(set(pairs)) == len(pairs)
    assert all(skill in names and broader in names and skill != broader for skill, broader in pairs)


def test_a_name_outside_the_vocabulary_stops_the_load(tmp_path, vocabulary):
    bad = tmp_path / "skill_implications.csv"
    bad.write_text("skill,implies\nPytorch,Machine learning\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Pytorch"):
        load_implications(bad, [skill for skill, _ in vocabulary])


def test_tools_imply_broader_skills_with_the_tools_line(vocabulary, implications, no_semantic):
    text = "Projects\nBuilt a churn model with PyTorch and scikit-learn\nDatabases: MySQL, PostgreSQL"
    matches = {m["skill"]: m for m in match_resume_skills(text, vocabulary, FakeEmbedder(), implications)}

    for skill in ("Machine learning", "Deep learning", "Python", "SQL", "Relational databases"):
        assert matches[skill]["method"] == "implied"
    assert matches["Machine learning"]["evidence"] == "Built a churn model with PyTorch and scikit-learn"
    assert matches["SQL"]["evidence"] == "Databases: MySQL, PostgreSQL"


def test_a_skill_found_by_the_rules_is_not_implied_again(vocabulary, implications, no_semantic):
    text = "Applied machine learning to sales data\nBuilt models with PyTorch"
    matches = match_resume_skills(text, vocabulary, FakeEmbedder(), implications)

    learning = [m for m in matches if m["skill"] == "Machine learning"]
    assert learning == [{"skill": "Machine learning", "evidence": "Applied machine learning to sales data", "method": "lexical"}]
    assert len({m["skill"] for m in matches}) == len(matches)


def test_implied_skills_do_not_imply_further(vocabulary, implications, no_semantic):
    # RAG implies Large language models; Large language models implies Natural language processing; RAG does not
    matches = {m["skill"]: m["method"] for m in match_resume_skills(
        "Built a RAG chatbot for customer service", vocabulary, FakeEmbedder(), implications)}

    assert matches["RAG"] == "lexical"
    assert matches["Large language models"] == "implied" and matches["Generative AI"] == "implied"
    assert "Natural language processing" not in matches