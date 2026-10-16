"""
PUT /candidate/target-role: save the role the signed-in candidate is aiming for.
"""

import base64
import json
from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query

INVALID_ROLE = {"message": "Choose a role from the list."}

def read_role_id(event):
    """(True, role_id) for a valid body, where a null role_id clears the role; (False, None) otherwise."""
    try:
        body = event.get("body") or ""
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        body = json.loads(body)
    except ValueError:
        return False, None
    if not isinstance(body, dict) or "role_id" not in body:
        return False, None

    role_id = body["role_id"]
    if role_id is None:
        return True, None
    is_valid = isinstance(role_id, int) and not isinstance(role_id, bool) and role_id > 0
    return (True, role_id) if is_valid else (False, None)

@api_handler
def handler(event, user):
    is_valid, role_id = read_role_id(event)
    if not is_valid:
        return 400, INVALID_ROLE

    role = None
    role_parameter = {"name": "role_id", "value": {"isNull": True}}
    if role_id is not None:
        role_parameter = {"name": "role_id", "value": {"longValue": role_id}}
        roles = run_query("SELECT role_id, title FROM roles WHERE role_id = :role_id", [role_parameter])
        if not roles:
            return 400, INVALID_ROLE
        role = roles[0]

    updated = run_query(
        "UPDATE users SET target_role_id = CAST(:role_id AS bigint) WHERE user_id = CAST(:user_id AS uuid) RETURNING user_id",
        [role_parameter, {"name": "user_id", "value": {"stringValue": user["user_id"]}}],
    )
    if not updated:
        return 404, {"message": "We couldn't find your account"}
    return 200, {"target_role": role}
