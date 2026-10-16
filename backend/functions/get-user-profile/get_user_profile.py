"""GET /candidate/profile and GET /recruiter/profile: the signed-in user's own account."""

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query

PROFILE_QUERY = """
SELECT u.email, u.full_name, u.account_type, u.company_name, u.target_role_id, r.title AS target_role_title
FROM users u LEFT JOIN roles r ON r.role_id = u.target_role_id
WHERE u.user_id = CAST(:user_id AS uuid)
"""

@api_handler
def handler(event, user):
    rows = run_query(PROFILE_QUERY, [{"name": "user_id", "value": {"stringValue": user["user_id"]}}])
    if not rows:
        return 404, {"message": "We couldn't find your account."}

    profile = rows[0]
    role_id = profile.pop("target_role_id", None)
    role_title = profile.pop("target_role_title", None)
    if user["role"] == "recruiter":
        return 200, profile

    profile.pop("company_name", None)
    profile["target_role"] = {"role_id": role_id, "title": role_title} if role_id else None
    return 200, profile