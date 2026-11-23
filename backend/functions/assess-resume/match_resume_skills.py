"""Skills evidenced in a resume, in three steps:
1. Rule-based: a skill's name or alias appears in a line of the resume.
2. Implied: a skill found in step 1 implies a broader one in the curated list (PyTorch -> Machine learning).
   The broader skill takes the line of the skill that implies it. Implied skills never imply further.
3. Semantic: for the skills still not found, the resume line closest in meaning, if it reaches the threshold.

The semantic match compares each resume line with each skill name using the skill embedding model, and keeps
the best line for a skill when its score reaches SEMANTIC_THRESHOLD. The score and threshold were chosen on
hand-labelled pairs (knowledge-base-pipeline/calibrate_semantic_threshold.py); setting the threshold to None
turns the semantic match off.
"""

import re

import numpy as np

from skill_matching import EDUCATION_LINE, find_skills

# "raw" is the cosine similarity; "relative" is how far a skill stands out for a line, in standard deviations
# above that line's mean similarity to all skills. Calibrated for granite-embedding-small-english-r2 (int8, commit
# 1dc7835) with the 281-skill vocabulary, as in kerjaready-skill-embedding-20261120 and later, on 264
# hand-labelled pairs from 20 test-split resumes: precision 0.84, recall 0.08 at a 0.80 precision target
# (knowledge-base-pipeline/reports/skill-match-calibration). A new model or vocabulary needs a new calibration.
SEMANTIC_SCORE = "raw"
SEMANTIC_THRESHOLD = 0.8862

MIN_WORDS = 4  # shorter lines (headings, comma-separated skill lists) are left to the rule-based match
MAX_LINES = 150
MAX_EVIDENCE_CHARS = 500
# A bullet glyph from the PDF ("•", "-", or a symbol-font bullet read as "ò" or "§"), followed by a space
LEADING_BULLET = re.compile(r"^[^A-Za-z0-9(\"'\s]\s+")


def evidence_text(line):
    """The line as the candidate sees it: no leading bullet glyph, at most MAX_EVIDENCE_CHARS."""
    return LEADING_BULLET.sub("", line.strip())[:MAX_EVIDENCE_CHARS]


def semantic_lines(text):
    """Lines worth comparing by meaning: unique, at least MIN_WORDS words, and not about a degree."""
    seen, lines = set(), []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if len(line.split()) < MIN_WORDS or EDUCATION_LINE.search(line) or line in seen:
            continue
        seen.add(line)
        lines.append(line)
        if len(lines) == MAX_LINES:
            break
    return lines


def line_skill_scores(lines, embedder):
    """Both scores as (lines x skills) matrices, with skills in embedder.skill_names order."""
    raw = embedder.embed(lines) @ embedder.skill_vectors.T
    spread = np.maximum(raw.std(axis=1, keepdims=True), 1e-6)
    return {"raw": raw, "relative": (raw - raw.mean(axis=1, keepdims=True)) / spread}


def match_resume_skills(text, vocabulary, embedder, implications):
    """[{"skill", "evidence", "method"}] for each skill evidenced in the resume: lexical, then implied, then semantic."""
    lexical = find_skills(text, vocabulary)
    matches = [{"skill": skill, "evidence": evidence_text(line), "method": "lexical"} for skill, line in lexical.items()]
    found = set(lexical)
    for skill, line in lexical.items():
        for broader in implications.get(skill, []):
            if broader not in found:
                found.add(broader)
                matches.append({"skill": broader, "evidence": evidence_text(line), "method": "implied"})

    lines = semantic_lines(text) if SEMANTIC_THRESHOLD is not None else []
    if not lines:
        return matches

    scores = line_skill_scores(lines, embedder)[SEMANTIC_SCORE]
    for column, skill in enumerate(embedder.skill_names):
        best = int(np.argmax(scores[:, column]))
        if skill not in found and scores[best, column] >= SEMANTIC_THRESHOLD:
            matches.append({"skill": skill, "evidence": evidence_text(lines[best]), "method": "semantic"})
    return matches