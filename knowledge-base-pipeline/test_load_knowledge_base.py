from load_knowledge_base import explanation_rows

PROFILE_KEYS = {("Backend Developer", "Python"), ("Backend Developer", "SQL")}
POSTING_IDS = {5101, 5102}


def explanation(role, skill, *posting_ids):
    return {
        "role": role, "skill": skill, "why_it_matters": f"Why {skill}.", "how_to_show": f"How {skill}.",
        "sources": [{"posting_id": posting_id, "line": f"Line {posting_id}"} for posting_id in posting_ids],
    }


def test_explanations_become_updates_and_source_rows():
    updates, sources, warnings = explanation_rows(
        [explanation("Backend Developer", "Python", 5101, 5102), explanation("Backend Developer", "SQL", 5102)],
        PROFILE_KEYS, POSTING_IDS,
    )
    assert updates == [
        ("Backend Developer", "Python", "Why Python.", "How Python."),
        ("Backend Developer", "SQL", "Why SQL.", "How SQL."),
    ]
    assert sources == [
        ("Backend Developer", "Python", 5101, "Line 5101"),
        ("Backend Developer", "Python", 5102, "Line 5102"),
        ("Backend Developer", "SQL", 5102, "Line 5102"),
    ]
    assert warnings == []


def test_explanations_that_no_longer_fit_are_left_out_with_a_warning():
    updates, sources, warnings = explanation_rows(
        [explanation("Backend Developer", "Python", 5101, 9999), explanation("Backend Developer", "Rust", 5101)],
        PROFILE_KEYS, POSTING_IDS,
    )
    assert updates == [("Backend Developer", "Python", "Why Python.", "How Python.")]
    assert sources == [("Backend Developer", "Python", 5101, "Line 5101")]
    assert warnings == [
        "Posting 9999 is not loaded, so Backend Developer | Python lost a source",
        "Backend Developer | Rust is not in the role profiles, so its explanation was left out",
        "1 role skills have no explanation and will show none",
    ]