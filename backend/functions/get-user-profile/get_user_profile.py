"""GET /candidate/profile and GET /recruiter/profile: the signed-in user's own account."""

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query

@api_handler
def handler(event, user):
    rows = run_query(
        "SELECT email, full_name, account_type, company_name"
        "FROM users WHERE user_id = CAST(:user_id AS uuid)",
        [{"name": "user_id", "value": {"stringValue": user["user_id"]}}],
    )
    if not rows:
        return 404, {"message": "We couldn't find your account."}

    profile = rows[0]
    if user["role"] != "recruiter":
        profile.pop("company_name", None)
    return 200, profile