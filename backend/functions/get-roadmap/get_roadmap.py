"""
GET /candidate/roadmap: the learning roadmap for the candidate's latest assessed resume and target role (KR-98).

Always 200, with:
- resume: the latest resume whose assessment finished (resume_id, file_name, assessed_at), or null
- target_role: role_id, title and posting_count, or null when the candidate hasn't chosen one
- run: the newest roadmap run for that resume and role (run_id, status, created_at, finished_at), or null when there
  has never been one. status is running, done or failed; a run stuck at running is reported as failed
  (kerjaready_shared/roadmap_runs.py)
- roadmap: the agent's output when run.status is done, else null

The saved output is the agent's own (roadmap_task.py). This route adds what comes from the database when the page
loads, so it never has to come from the model:
- each resume step: level, level_label and next_label from the resume's ratings and the rubric
- each skill milestone: postings and role_postings (how many of the role's postings ask for the skill), why_it_matters
  (the stored KR-100 explanation, as on the Skill Gap page, or null) and learn_after (the other milestones its
  learning_order names, as one phrase, or null)
"""

import json
import re

from kerjaready_shared import roadmap_runs
from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.rubric import RUBRIC

# The four levels only
RATINGS = """
SELECT a1_rating, a2_rating, a3_rating, b2_rating
FROM resume_ratings
WHERE resume_id = :resume_id
"""
ROLE_SKILLS = """
SELECT s.name, CAST(rq.demand_share AS double precision) AS demand_share, rq.why_it_matters
FROM role_skills rq
JOIN skills s ON s.skill_id = rq.skill_id
WHERE rq.role_id = :role_id
"""
TOP_LEVEL = 3


def mentions(text, skill):
    """Whether text names the skill as a whole word, so that Go does not match Google."""
    return re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", text, re.IGNORECASE) is not None


def joined(names):
    """["A"] -> "A", ["A", "B"] -> "A and B", ["A", "B", "C"] -> "A, B and C"."""
    if len(names) < 2:
        return names[0] if names else None
    return ", ".join(names[:-1]) + " and " + names[-1]


def resume_steps(steps, resume_id):
    rows = run_query(RATINGS, [{"name": "resume_id", "value": {"longValue": resume_id}}])
    ratings = rows[0] if rows else {}
    criteria = {name.casefold(): (column, labels) for column, name, _, labels, _ in RUBRIC}
    result = []
    for step in steps:
        column, labels = criteria.get(step["criterion"].casefold(), (None, None))
        level = ratings.get(column) if column else None
        # A step the rubric or the ratings can't place is left out rather than shown without its levels
        if level is None or level >= TOP_LEVEL:
            continue
        result.append({**step, "level": level, "level_label": labels[level], "next_label": labels[level + 1]})
    return result


def skill_milestones(milestones, role):
    rows = run_query(ROLE_SKILLS, [{"name": "role_id", "value": {"longValue": role["role_id"]}}])
    profile = {row["name"].casefold(): row for row in rows}
    names = [milestone["skill"] for milestone in milestones]
    result = []
    for milestone in milestones:
        skill = milestone["skill"]
        found = profile.get(skill.casefold())
        note = milestone.get("learning_order") or ""
        earlier = [other for other in names if other.casefold() != skill.casefold() and mentions(note, other)]
        result.append({
            **milestone,
            "postings": round(found["demand_share"] * role["posting_count"]) if found else 0,
            "role_postings": role["posting_count"],
            "why_it_matters": found.get("why_it_matters") if found else None,
            "learn_after": joined(earlier),
        })
    return result


@api_handler
def handler(event, user):
    resume, role = roadmap_runs.context(user["user_id"])
    result = {"resume": resume, "target_role": role, "run": None, "roadmap": None}
    if resume is None or role is None:
        return 200, result

    row = roadmap_runs.latest_run(resume, role)
    if row is None:
        return 200, result
    result["run"] = roadmap_runs.run_summary(row)
    if row["status"] == roadmap_runs.DONE and row.get("output"):
        output = json.loads(row["output"])
        result["roadmap"] = {
            "resume_steps": resume_steps(output.get("resume_steps", []), resume["resume_id"]),
            "skill_milestones": skill_milestones(output.get("skill_milestones", []), role),
        }
    return 200, result