import json

import pandas as pd

from prepare_skill_explanation_inputs import (
    build_records,
    clean_line,
    is_full_line,
    main,
    role_file_name,
)
from skill_explanation_prompt import MAX_LINES

ROLE_SKILLS = pd.DataFrame([
    {"role_title": "Backend Developer", "skill": "Python", "posting_count": 7, "role_postings": 10, "demand_share": 0.7},
    {"role_title": "AI/ML Engineer", "skill": "Python", "posting_count": 2, "role_postings": 4, "demand_share": 0.5},
])
POSTINGS = pd.DataFrame(
    [{"job_id": i, "role_title": "Backend Developer", "job_title": "Dev", "listing_date": f"2026-01-{i:02d}",
      "description": "x"} for i in range(1, 8)]
    + [{"job_id": 20 + i, "role_title": "AI/ML Engineer", "job_title": "ML", "listing_date": "2025-06-01",
        "description": "x"} for i in range(1, 3)]
)
BACKEND_LINES = {
    1: "• Build REST APIs in Python with Django for our payment platform.",
    2: "Python, Java, Go, Rust",
    3: "Write Python services that read data from message queues every day.",
    4: "Write Python services that read data from message queues every day.",
    5: "Use Python and FastAPI to build internal tools for the operations team.",
    6: "Contact hr@example.com or visit https://example.com to apply with Python experience today.",
    7: "Maintain Python scripts that automate the nightly database backups for clients.",
}
POSTING_SKILLS = pd.DataFrame(
    [{"job_id": i, "role_title": "Backend Developer", "skill": "Python", "evidence_line": line}
     for i, line in BACKEND_LINES.items()]
    + [{"job_id": i, "role_title": "Backend Developer", "skill": "Django", "evidence_line": "Django"} for i in (1, 5, 7)]
    + [{"job_id": 1, "role_title": "Backend Developer", "skill": "Go", "evidence_line": "Go"}]
    + [{"job_id": 20 + i, "role_title": "AI/ML Engineer", "skill": "Python",
        "evidence_line": "Train machine learning models in Python with PyTorch for vision tasks."} for i in (1, 2)]
    + [{"job_id": 20 + i, "role_title": "AI/ML Engineer", "skill": "PyTorch", "evidence_line": "PyTorch"} for i in (1, 2)]
)


def records_by_role():
    return {r["role"]: r for r in build_records(ROLE_SKILLS, POSTING_SKILLS, POSTINGS)}


def test_role_file_names():
    assert role_file_name("UI/UX Designer") == "ui-ux-designer"
    assert role_file_name("Network / Systems Engineer") == "network-systems-engineer"


def test_clean_line_removes_bullets_contacts_and_links():
    assert clean_line("• Build APIs") == "Build APIs"
    assert clean_line("Email hr@example.com or see https://example.com") == "Email [email] or see [link]"
    long = clean_line("word " * 100)
    assert len(long) <= 304 and long.endswith(" ...")


def test_a_skill_list_is_not_a_full_line():
    assert not is_full_line("Python, Java, Go, Rust, C++, SQL, Linux, Docker")
    assert is_full_line("Build REST APIs in Python with Django for our payment platform.")


def test_each_role_gets_its_own_lines_and_related_skills():
    records = records_by_role()
    backend, ai = records["Backend Developer"], records["AI/ML Engineer"]
    assert all(line["posting_id"] < 20 for line in backend["lines"])
    assert all(line["posting_id"] > 20 for line in ai["lines"])
    assert backend["related"] == [{"skill": "Django", "postings": 3}]  # Go is in only 1 posting
    assert ai["related"] == [{"skill": "PyTorch", "postings": 2}]
    assert "Asked for in 7 of 10 Backend Developer postings (70%)." in backend["prompt"]


def test_lines_prefer_full_lines_then_newest_and_skip_repeats():
    lines = records_by_role()["Backend Developer"]["lines"]
    ids = [line["posting_id"] for line in lines]
    assert len(lines) == MAX_LINES
    # Full lines newest first; posting 3 repeats posting 4's text; the bare skill list (posting 2) misses the cut
    assert ids == [7, 6, 5, 4, 1]
    assert lines[ids.index(6)]["text"].startswith("Contact [email] or visit [link]")


def test_main_writes_one_file_per_role(tmp_path, monkeypatch):
    role_skills, posting_skills, postings = (tmp_path / name for name in ("rs.csv", "ps.csv", "p.csv"))
    ROLE_SKILLS.to_csv(role_skills, index=False)
    POSTING_SKILLS.to_csv(posting_skills, index=False)
    POSTINGS.to_csv(postings, index=False)
    monkeypatch.setattr("sys.argv", ["prepare", str(role_skills), str(posting_skills), str(postings),
                                     str(tmp_path / "out")])
    main()
    files = sorted(p.name for p in (tmp_path / "out" / "inputs").iterdir())
    assert files == ["ai-ml-engineer.jsonl", "backend-developer.jsonl"]
    record = json.loads((tmp_path / "out" / "inputs" / "backend-developer.jsonl").read_text(encoding="utf-8"))
    assert set(record) == {"role", "skill", "skill_postings", "role_postings", "lines", "related", "prompt"}