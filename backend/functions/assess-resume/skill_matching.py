"""Find skills from the curated vocabulary in text, line by line.

Used by kerjaready-assess-resume for resumes and by knowledge-base-pipeline/extract_role_skills.py for job
postings, so resumes and role profiles use one definition of each skill. Reads the CSV without pandas,
which the Lambda container does not install.
"""

import csv
import re

# Phrases removed before matching, because they contain a skill name with another meaning
BLOCKED_PHRASES = re.compile(
    r"cisco ios|go-live|go live|go-to-market|go to market|san francisco|r&d|"
    r"ui/ux designers?|ux/ui designers?|ux designers?",
    re.IGNORECASE,
)
# Field-of-study names count as skills only outside education requirement lines
FIELD_OF_STUDY_SKILLS = {"Data science", "Statistics", "Data analysis", "Cybersecurity", "Machine learning"}
EDUCATION_LINE = re.compile(r"degree|diploma|bachelor|master'?s|ph\.?d|graduate in|graduated in|qualification", re.I)


def split_aliases(value):
    return [alias.strip() for alias in value.split(";") if alias.strip()] if isinstance(value, str) else []


def alias_pattern(aliases, case_sensitive):
    alternatives = "|".join(re.escape(alias) for alias in sorted(aliases, key=len, reverse=True))
    if case_sensitive:
        # "R" or "Go" must not touch &, - or ', so "R&D" and "C-level" are not skills
        return re.compile(rf"(?<![\w+#&'-])(?:{alternatives})(?![\w+#&'-])")
    return re.compile(rf"(?<![\w+#])(?:{alternatives})(?![\w+#])", re.IGNORECASE)


def load_vocabulary(vocabulary_csv):
    """Each skill with its compiled alias patterns, in file order."""
    vocabulary = []
    with open(vocabulary_csv, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            patterns = []
            if split_aliases(row["aliases"]):
                patterns.append(alias_pattern(split_aliases(row["aliases"]), case_sensitive=False))
            if split_aliases(row["case_sensitive_aliases"]):
                patterns.append(alias_pattern(split_aliases(row["case_sensitive_aliases"]), case_sensitive=True))
            vocabulary.append((row["skill"], patterns))
    return vocabulary


def load_implications(implications_csv, skill_names):
    """{skill: [broader skills it implies]} from the curated list, in file order. Every name must be a vocabulary skill."""
    known, implications = set(skill_names), {}
    with open(implications_csv, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            unknown = {row["skill"], row["implies"]} - known
            if unknown:
                raise ValueError(f"skill_implications.csv names skills not in the vocabulary: {sorted(unknown)}")
            implications.setdefault(row["skill"], []).append(row["implies"])
    return implications


def find_skills(text, vocabulary):
    """Each skill found in the text, with the first line it appears in."""
    found = {}
    for line in text.splitlines():
        searchable = BLOCKED_PHRASES.sub(" ", line)
        education = bool(EDUCATION_LINE.search(searchable))
        for skill, patterns in vocabulary:
            if skill in found or (education and skill in FIELD_OF_STUDY_SKILLS):
                continue
            if any(pattern.search(searchable) for pattern in patterns):
                found[skill] = line.strip()
    return found