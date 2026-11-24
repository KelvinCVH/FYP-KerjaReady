"""The guidance agent's tools (KR-144): the resume's assessment ratings and its skill gap for the target role.

Every tool is bound to the run's resume and role, so the model can never ask about another candidate's data.
The model is reached through global cross-Region inference, so the tools return no resume text, evidence lines,
links, language errors, file names or personal details: only criterion levels, skill names, match types and
posting counts.
"""

import json

from kerjaready_shared.data_api import run_query
from strands import tool

# Rubric v1.0 as candidates see it (frontend/src/lib/rubric.ts): names and level labels, never the codes
RUBRIC = [
    ("a1_rating", "Work Evidence", "Do the entries say what was built or done, and with which technologies?",
     ["Not shown", "Limited", "Clear", "Strong"]),
    ("a2_rating", "Outcome", "Does the resume say what the work achieved?",
     ["Not shown", "Limited", "Clear", "Strong"]),
    ("a3_rating", "Skill in Use", "Are skills shown being used, not just listed?",
     ["Not shown", "Limited", "Clear", "Strong"]),
    ("b2_rating", "Language Quality", "Is the writing free of spelling and grammar errors?",
     ["Hard to read", "Several errors", "Minor errors", "No errors found"]),
]
MATCH_TYPES = {"lexical": "named in the resume", "implied": "shown through a related tool", "semantic": "similar wording"}

# Only the four levels: the work link and the language errors hold resume text
RATINGS = """
SELECT a1_rating, a2_rating, a3_rating, b2_rating
FROM resume_ratings
WHERE resume_id = :resume_id
"""
ROLE = """
SELECT ro.title, (SELECT count(*) FROM job_postings jp WHERE jp.role_id = ro.role_id) AS posting_count
FROM roles ro
WHERE ro.role_id = :role_id
"""
# The match method only: the evidence line is resume text
SKILLS = """
SELECT s.name, CAST(rq.demand_share AS double precision) AS demand_share, rk.match_method
FROM role_skills rq
JOIN skills s ON s.skill_id = rq.skill_id
LEFT JOIN resume_skills rk ON rk.skill_id = rq.skill_id AND rk.resume_id = :resume_id
WHERE rq.role_id = :role_id
ORDER BY rq.demand_share DESC, s.name
"""


def _id(name, value):
    return [{"name": name, "value": {"longValue": value}}]


def assessment_ratings(resume_id):
    rows = run_query(RATINGS, _id("resume_id", resume_id))
    if not rows:
        return {"error": "This resume has no assessment ratings."}
    return {"criteria": [
        {"name": name, "question": question, "level": rows[0][column], "out_of": 3,
         "label": labels[rows[0][column]]}
        for column, name, question, labels in RUBRIC
    ]}


def skill_gap(resume_id, role_id):
    roles = run_query(ROLE, _id("role_id", role_id))
    if not roles:
        return {"error": "The target role was not found."}
    postings = roles[0]["posting_count"]
    result = {"target_role": roles[0]["title"], "role_postings": postings, "evidenced": [], "not_evidenced": []}
    for row in run_query(SKILLS, _id("resume_id", resume_id) + _id("role_id", role_id)):
        entry = {
            "skill": row["name"],
            "postings": round(row["demand_share"] * postings),
            "share_percent": round(row["demand_share"] * 100),
        }
        if row.get("match_method") is None:
            result["not_evidenced"].append(entry)
        else:
            result["evidenced"].append({**entry, "match": MATCH_TYPES[row["match_method"]]})
    return result


def make_tools(resume_id, role_id):
    @tool
    def get_assessment_ratings() -> str:
        """Get the candidate's resume assessment: four criteria, each rated from 0 to 3.

        Work Evidence, Outcome and Skill in Use rate the resume's content; Language Quality rates its writing.
        A low level means the resume does not show that quality yet, not that the candidate lacks it.
        """
        return json.dumps(assessment_ratings(resume_id))

    @tool
    def get_skill_gap() -> str:
        """Get the skills the candidate's target role asks for, split into evidenced and not evidenced.

        Skills come from entry-level job postings in Malaysia for the role, most often asked first, with how many
        postings ask for each. A skill that is not evidenced is one the resume does not show, not one the
        candidate lacks.
        """
        return json.dumps(skill_gap(resume_id, role_id))

    return [get_assessment_ratings, get_skill_gap]