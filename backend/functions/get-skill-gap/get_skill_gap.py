"""
GET /candidate/resumes/{resume_id}/skill-gap: the skills in the candidate's saved target role profile, split into
those evidenced in this resume and those not evidenced, each group ordered by demand share (highest first).

A skill is evidenced when the assessment found it in the resume (a row in resume_skills: lexical, implied or semantic),
and the matching resume line comes back with it. A skill that was not found is "not evidenced in the resume":
the candidate may still have it.

Every skill has demand_share, the share of the role's postings that ask for it, and postings, the number of those
postings. demand_share is that number divided by posting_count, stored to 4 decimal places, so
round(demand_share * posting_count) gives the number back exactly while a role has fewer than 10,000 postings.

target_role also says where those numbers come from: posting_count entry-level JobStreet postings in Malaysia, posted
from first_posted to last_posted (the earliest and latest posted_date, as "YYYY-MM-DD"). Both dates are null when
the role has no postings.

Each skill not evidenced also carries its explanation (KR-100), written once for the role from its job postings:
why_it_matters, how_to_show and sources, the posting lines it is based on, newest first. why_it_matters and
how_to_show are null, and sources empty, until the knowledge base load adds the explanations.

- 404 when the resume is missing, still uploading or another candidate's
- 409 when its assessment has not finished, because skills are found during the assessment
- target_role null and two empty groups when the candidate has not chosen a target role
"""

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.resume_status import DONE, UPLOADING

NOT_FOUND = {"message": "We couldn’t find that resume."}
NOT_ASSESSED = {"message": "This resume hasn’t finished its assessment yet."}

# One pass over the role's postings gives their count and date range. to_char keeps the dates as "YYYY-MM-DD";
# both are NULL when the role has no postings.
RESUME_AND_ROLE = """
SELECT r.status, u.target_role_id AS role_id, ro.title,
       p.posting_count, p.first_posted, p.last_posted
FROM resumes r
JOIN users u ON u.user_id = r.candidate_id
LEFT JOIN roles ro ON ro.role_id = u.target_role_id
LEFT JOIN LATERAL (
    SELECT count(*) AS posting_count,
           to_char(min(jp.posted_date), 'YYYY-MM-DD') AS first_posted,
           to_char(max(jp.posted_date), 'YYYY-MM-DD') AS last_posted
    FROM job_postings jp
    WHERE jp.role_id = u.target_role_id
) p ON true
WHERE r.resume_id = :resume_id AND r.candidate_id = CAST(:user_id AS uuid)
"""

# Every skill in the role profile once; the LEFT JOIN brings the resume's evidence where there is some
ROLE_SKILLS = """
SELECT s.skill_id, s.name, CAST(rq.demand_share AS double precision) AS demand_share,
       rk.evidence_excerpt AS evidence, rk.match_method, rq.why_it_matters, rq.how_to_show
FROM role_skills rq
JOIN skills s ON s.skill_id = rq.skill_id
LEFT JOIN resume_skills rk ON rk.skill_id = rq.skill_id AND rk.resume_id = :resume_id
WHERE rq.role_id = :role_id
ORDER BY rq.demand_share DESC, s.name
"""

# The posting lines behind the role's skill explanations, newest posting first
EXPLANATION_SOURCES = """
SELECT src.skill_id, src.posting_id, src.line, jp.job_title, to_char(jp.posted_date, 'YYYY-MM-DD') AS posted_date
FROM role_skill_sources src
JOIN job_postings jp ON jp.posting_id = src.posting_id
WHERE src.role_id = :role_id
ORDER BY src.skill_id, jp.posted_date DESC, src.posting_id
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

    posting_count = row["posting_count"]
    result["target_role"] = {
        "role_id": row["role_id"],
        "title": row["title"],
        "posting_count": posting_count,
        "first_posted": row.get("first_posted"),
        "last_posted": row.get("last_posted"),
    }
    skills = run_query(ROLE_SKILLS, [_long("resume_id", resume_id), _long("role_id", row["role_id"])])
    sources = {}
    if any(skill.get("evidence") is None for skill in skills):
        for source in run_query(EXPLANATION_SOURCES, [_long("role_id", row["role_id"])]):
            sources.setdefault(source["skill_id"], []).append({
                "posting_id": source["posting_id"],
                "line": source["line"],
                "job_title": source["job_title"],
                "posted_date": source["posted_date"],
            })

    for skill in skills:
        entry = {
            "skill_id": skill["skill_id"],
            "name": skill["name"],
            "demand_share": skill["demand_share"],
            "postings": round(skill["demand_share"] * posting_count),
        }
        if skill.get("evidence") is None:
            result["not_evidenced"].append({
                **entry,
                "why_it_matters": skill.get("why_it_matters"),
                "how_to_show": skill.get("how_to_show"),
                "sources": sources.get(skill["skill_id"], []),
            })
        else:
            result["evidenced"].append({**entry, "evidence": skill["evidence"], "match_method": skill["match_method"]})
    return 200, result