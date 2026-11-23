import json

import pandas as pd
import pytest

from check_skill_explanations import check_role, main, write_sample
from skill_explanation_prompt import build_prompt

LINES = [(5101, "Develop REST APIs in Python with Django or FastAPI.")]


def record(role, skill):
    return {
        "role": role, "skill": skill, "skill_postings": 41, "role_postings": 84,
        "lines": [{"posting_id": i, "text": t} for i, t in LINES], "related": [{"skill": "Django", "postings": 22}],
        "prompt": build_prompt(role, skill, 41, 84, LINES, [("Django", 22)]),
    }


def reply(role, skill, **changes):
    return {
        "role": role, "skill": skill,
        "why_it_matters": f"{role} postings ask for {skill} to build web APIs. It often comes with Django.",
        "how_to_show": f"If you have this skill, name {skill} in a project line with the API you built.",
        "source_posting_ids": [5101],
        **changes,
    }


def write(folder, kind, name, rows):
    path = folder / kind / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_a_role_with_no_outputs_is_reported(tmp_path):
    inputs = write(tmp_path, "inputs", "backend-developer", [record("Backend Developer", "Python")])
    problems, passed = check_role(inputs, tmp_path / "outputs" / "backend-developer.jsonl")
    assert problems == ["backend-developer.jsonl: no outputs yet (1 skills)"]
    assert passed == []


def test_missing_extra_repeated_and_broken_explanations_are_reported(tmp_path):
    inputs = write(tmp_path, "inputs", "backend-developer",
                   [record("Backend Developer", "Python"), record("Backend Developer", "SQL")])
    outputs = write(tmp_path, "outputs", "backend-developer", [
        reply("Backend Developer", "Python"),
        reply("Backend Developer", "Python"),
        reply("Backend Developer", "Rust"),
        {**reply("Backend Developer", "Python"), "extra": 1},
    ])
    problems, passed = check_role(inputs, outputs)
    assert len(passed) == 1
    text = "\n".join(problems)
    assert "explained more than once" in text
    assert "(Backend Developer | Rust): no input for this role and skill" in text
    assert "fields must be exactly" in text
    assert "no explanation for SQL" in text


def test_rule_breaks_name_the_line(tmp_path):
    inputs = write(tmp_path, "inputs", "backend-developer", [record("Backend Developer", "Python")])
    outputs = write(tmp_path, "outputs", "backend-developer",
                    [reply("Backend Developer", "Python", why_it_matters="You lack Python. Postings ask for it.")])
    problems, _ = check_role(inputs, outputs)
    assert problems == [
        "backend-developer.jsonl line 1 (Backend Developer | Python): why_it_matters suggests the reader lacks the skill"
    ]


def test_sample_spreads_across_roles(tmp_path):
    passed = [(record(role, f"Skill{i}"), reply(role, f"Skill{i}")) for role in ("A", "B", "C") for i in range(5)]
    path = tmp_path / "review-sample.csv"
    write_sample(passed, 6, path)
    sample = pd.read_csv(path)
    assert len(sample) == 6
    assert sample["role"].value_counts().to_dict() == {"A": 2, "B": 2, "C": 2}
    assert sample["source_lines"].iloc[0].startswith("[5101] Develop REST APIs")
    assert {"grounded", "useful_advice", "notes"} <= set(sample.columns)


def test_main_exits_with_1_while_problems_remain(tmp_path, monkeypatch):
    write(tmp_path, "inputs", "backend-developer", [record("Backend Developer", "Python")])
    monkeypatch.setattr("sys.argv", ["check", str(tmp_path)])
    with pytest.raises(SystemExit) as stop:
        main()
    assert stop.value.code == 1

    write(tmp_path, "outputs", "backend-developer", [reply("Backend Developer", "Python")])
    monkeypatch.setattr("sys.argv", ["check", str(tmp_path), "--sample", "40"])
    main()
    assert len(pd.read_csv(tmp_path / "review-sample.csv")) == 1