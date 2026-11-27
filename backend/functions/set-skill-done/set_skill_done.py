"""
PUT and DELETE /candidate/done-skills/{skill_id}: mark a skill on the Learning Roadmap done, or undo it (KR-99).

A done mark belongs to the candidate and the skill, not to a roadmap run, so it stays through Regenerate, a new resume
and a new target role. Both methods are idempotent: marking a done skill again, or undoing one that isn't done, still
succeeds.

- 200 {"skill_id": 12, "done": true} after PUT, {"skill_id": 12, "done": false} after DELETE
- 400 when skill_id is not a positive whole number
- 404 when there is no such skill
"""

import re

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query
from kerjaready_shared.roadmap_runs import user_parameter

INVALID_SKILL = {"message": "Choose a skill from your roadmap."}
NO_SKILL = {"message": "We couldn't find this skill."}
NOT_ALLOWED = {"message": "Use PUT to mark a skill done or DELETE to undo it."}

# A positive bigint in ASCII digits. str.isdigit() would also accept digits such as "²", which int() rejects.
SKILL_ID = re.compile(r"[1-9][0-9]{0,17}")

SKILL = "SELECT skill_id FROM skills WHERE skill_id = :skill_id"
MARK = """
INSERT INTO done_skills (candidate_id, skill_id) VALUES (CAST(:user_id AS uuid), :skill_id)
ON CONFLICT DO NOTHING
"""
UNMARK = """
DELETE FROM done_skills WHERE candidate_id = CAST(:user_id AS uuid) AND skill_id = :skill_id
"""
# Method -> (statement, whether the skill is done afterwards)
WRITES = {"PUT": (MARK, True), "DELETE": (UNMARK, False)}


@api_handler
def handler(event, user):
    method = event.get("routeKey", "").split(" ", 1)[0]
    if method not in WRITES:
        return 405, NOT_ALLOWED

    value = (event.get("pathParameters") or {}).get("skill_id") or ""
    if not SKILL_ID.fullmatch(value):
        return 400, INVALID_SKILL
    skill_id = int(value)
    skill_parameter = {"name": "skill_id", "value": {"longValue": skill_id}}

    if not run_query(SKILL, [skill_parameter]):
        return 404, NO_SKILL

    sql, done = WRITES[method]
    run_query(sql, [user_parameter(user["user_id"]), skill_parameter])
    return 200, {"skill_id": skill_id, "done": done}
