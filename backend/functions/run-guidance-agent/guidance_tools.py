"""The guidance agent's tools: the resume's assessment ratings and its skill gap for the target role (KR-144),
and market context for chosen skills: why the role asks for each and the job posting lines behind it (KR-146).

Every tool is bound to the run's resume and role, so the model can never ask about another candidate's data.
The model is reached through global cross-Region inference, so the tools return no resume text, evidence lines,
links, language errors, file names or personal details: only criterion levels, skill names, match types,
posting counts, the stored skill explanations and job posting lines.
"""

import json

from kerjaready_shared.data_api import run_query
from strands import tool

# Rubric v1.0 as candidates see it (frontend/src/lib/rubric.ts): names, level labels and what the next level needs,
# never the codes. The next-level text is fixed rubric wording, so the agent never has to invent the rubric.
RUBRIC = [
    ("a1_rating", "Work Evidence", "Do the entries say what was built or done, and with which technologies?",
     ["Not shown", "Limited", "Clear", "Strong"],
     ["At least one job, internship or project that says what you built or did and which technologies you used.",
      "More than half of your entries name the specific thing you built or did (a system, feature, report or "
      "script) and the tools you used.",
      "A link to the work itself in at least one entry: a code repository, live demo or portfolio site. A GitHub "
      "profile link alone doesn't count.",
      None]),
    ("a2_rating", "Outcome", "Does the resume say what the work achieved?",
     ["Not shown", "Limited", "Clear", "Strong"],
     ["At least one entry that says what the work achieved: something became faster, more accurate or automated, "
      "or users or a client adopted it.",
      "A concrete result in more than half of your entries. \"Built a dashboard\" is a task; \"The sales team now "
      "uses the dashboard for weekly reviews\" is a result.",
      "At least one result measured with a number, such as \"cut the report time from 6 hours to 2\". Team size or "
      "the number of reports doesn't count.",
      None]),
    ("a3_rating", "Skill in Use", "Are skills shown being used, not just listed?",
     ["Not shown", "Limited", "Clear", "Strong"],
     ["Tools mentioned inside your entry descriptions, not only in the skills list.",
      "More than half of your entries say what a tool was used for, such as \"Used Python to automate the monthly "
      "report\".",
      "Nearly all entries give each tool its own job: \"Built the interface with React and the API with Spring "
      "Boot\", not \"using Java, Spring and Hibernate\".",
      None]),
    ("b2_rating", "Language Quality", "Is the writing free of spelling and grammar errors?",
     ["Hard to read", "Several errors", "Minor errors", "No errors found"],
     [None,
      "No more than two spelling, grammar or product-name errors. The Resume page lists the errors found.",
      "No spelling, grammar or product-name errors. The Resume page lists the errors found.",
      None]),
]
# The roadmap covers six skills, so one call can look them all up
MAX_CONTEXT_SKILLS = 6
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

# The stored explanations (KR-100) for every skill in the role profile
EXPLANATIONS = """
SELECT s.skill_id, s.name, CAST(rq.demand_share AS double precision) AS demand_share,
       rq.why_it_matters, rq.how_to_show
FROM role_skills rq
JOIN skills s ON s.skill_id = rq.skill_id
WHERE rq.role_id = :role_id
"""
# The job posting lines the explanations are based on, newest posting first
SOURCES = """
SELECT src.skill_id, src.posting_id, src.line, jp.job_title, to_char(jp.posted_date, 'YYYY-MM') AS posted_month
FROM role_skill_sources src
JOIN job_postings jp ON jp.posting_id = src.posting_id
WHERE src.role_id = :role_id
ORDER BY src.skill_id, jp.posted_date DESC, src.posting_id
"""


def _id(name, value):
    return [{"name": name, "value": {"longValue": value}}]


def assessment_ratings(resume_id):
    rows = run_query(RATINGS, _id("resume_id", resume_id))
    if not rows:
        return {"error": "This resume has no assessment ratings."}
    return {"criteria": [
        {"name": name, "question": question, "level": rows[0][column], "out_of": 3,
         "label": labels[rows[0][column]], "next_level": next_levels[rows[0][column]]}
        for column, name, question, labels, next_levels in RUBRIC
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


def market_context(role_id, skills):
    """Explanations and posting lines for up to MAX_CONTEXT_SKILLS of the role's skills, matched by name."""
    roles = run_query(ROLE, _id("role_id", role_id))
    if not roles:
        return {"error": "The target role was not found."}
    postings = roles[0]["posting_count"]
    profile = {row["name"].casefold(): row for row in run_query(EXPLANATIONS, _id("role_id", role_id))}

    found, not_in_role = [], []
    for name in dict.fromkeys(str(skill).strip() for skill in skills):
        row = profile.get(name.casefold())
        if row is None:
            not_in_role.append(name)
        elif row not in found:
            found.append(row)
    wanted = found[:MAX_CONTEXT_SKILLS]

    lines = {}
    if wanted:
        for source in run_query(SOURCES, _id("role_id", role_id)):
            lines.setdefault(source["skill_id"], []).append({
                "posting_id": source["posting_id"],
                "line": source["line"],
                "job_title": source["job_title"],
                "posted": source["posted_month"],
            })

    result = {"skills": [
        {
            "skill": row["name"],
            "postings": round(row["demand_share"] * postings),
            "role_postings": postings,
            "why_it_matters": row["why_it_matters"],
            "how_to_show": row["how_to_show"],
            "posting_lines": lines.get(row["skill_id"], []),
        }
        for row in wanted
    ]}
    if not_in_role:
        result["not_in_role_profile"] = not_in_role
    if len(found) > MAX_CONTEXT_SKILLS:
        result["note"] = f"Only the first {MAX_CONTEXT_SKILLS} skills were looked up; ask again for the rest."
    return result


def make_tools(resume_id, role_id):
    @tool
    def get_assessment_ratings() -> str:
        """Get the candidate's resume assessment: four criteria, each rated from 0 to 3.

        Work Evidence, Outcome and Skill in Use rate the resume's content; Language Quality rates its writing.
        next_level is the rubric's own wording for what reaching the next level needs (null at the top level).
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

    @tool
    def get_market_context(skills: list[str]) -> str:
        """Get why the target role asks for each skill, how to show it in a resume, and the job posting lines
        behind it.

        The explanations were written once with AI from the role's job postings; each posting line comes with its
        posting_id, job title and month. Cite posting_id values from here when you use these lines.

        Args:
            skills: Up to 6 skill names from the target role's profile, as get_skill_gap names them.
        """
        return json.dumps(market_context(role_id, skills))

    return [get_assessment_ratings, get_skill_gap, get_market_context]