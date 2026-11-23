"""
GET /candidate/resumes/{resume_id}/skill-gap: the skills in the candidate's saved target role profile, split into
those evidenced in this resume and those not evidenced, each group ordered by demand share (highest first).

A skill is evidenced when the assessment found it in the resume (a row in resume_skills,lexical, implied, or semantic),
and the matching resume line comes back with it. A skill that was not found is "not evidenced in the resume":
the candidate may still have it.

- 404 when the resume is missing, still uploading or another candidate's
- 409 when its assessment has not finished, because skills are found during the assessment
- target_role null and two empty groups when the candidate has not chosen a target role
"""

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.resume_status import DONE, UPLOADING

NOT_FOUND = {"message": "We couldn’t find that resume."}
NOT_ASSESSED = {"message": "This resume hasn’t finished its assessment yet."}

RESUME_AND_ROLE = """
SELECT r.status, u.target_role_id AS role_id, ro.title,
       (SELECT count(*) FROM job_postings p WHERE p.role_id = u.target_role_id) AS posting_count
FROM resumes r
JOIN users u ON u.user_id = r.candidate_id
LEFT JOIN roles ro ON ro.role_id = u.target_role_id
WHERE r.resume_id = :resume_id AND r.candidate_id = CAST(:user_id AS uuid)
"""

# Every skill in the role profile once; the LEFT JOIN brings the resume's evidence where there is some
ROLE_SKILLS = """
SELECT s.skill_id, s.name, CAST(rq.demand_share AS double precision) AS demand_share,
       rk.evidence_excerpt AS evidence, rk.match_method
FROM role_skills rq
JOIN skills s ON s.skill_id = rq.skill_id
LEFT JOIN resume_skills rk ON rk.skill_id = rq.skill_id AND rk.resume_id = :resume_id
WHERE rq.role_id = :role_id
ORDER BY rq.demand_share DESC, s.name
"""


def _long(name, value):
    return {"name": name, "value": {"longValue": value}}


@api_handler
def handler(event, user):
    value = (event.get("pathParameters") or {}).get("resume_id") or ""
    if not value.isdigit():
        return 404, NOT_FOUND
    resume_id = int(value)

    rows = run_query(RESUME_AND_ROLE, [_long("resume_id", resume_id),
                                       {"name": "user_id", "value": {"stringValue": user["user_id"]}}])
    if not rows or rows[0]["status"] == UPLOADING:
        return 404, NOT_FOUND
    row = rows[0]
    if row["status"] != DONE:
        return 409, NOT_ASSESSED

    result = {"resume_id": resume_id, "target_role": None, "evidenced": [], "not_evidenced": []}
    if row.get("role_id") is None:
        return 200, result

    result["target_role"] = {"role_id": row["role_id"], "title": row["title"], "posting_count": row["posting_count"]}
    for skill in run_query(ROLE_SKILLS, [_long("resume_id", resume_id), _long("role_id", row["role_id"])]):
        entry = {"skill_id": skill["skill_id"], "name": skill["name"], "demand_share": skill["demand_share"]}
        if skill.get("evidence") is None:
            result["not_evidenced"].append(entry)
        else:
            result["evidenced"].append({**entry, "evidence": skill["evidence"], "match_method": skill["match_method"]})
    return 200, result