"""
Role checks and JSON response for API routes
The first path segment decides the role:
/candidate/* -> candidate group, /recruiter/* -> recruiter group
and any other signed-in route needs one of the two
"""

import functools
import json
import traceback
from kerjaready_shared.data_api import DatabaseStarting

ROLES = ("candidate", "recruiter")

class AccessDenied(Exception):
    """The signed-in user may not call this route"""

def parse_groups(value):
    """API Gateway may pass cognito: groups as a list, a JSON string or "[a b]."""
    if isinstance(value, list):
        return [str(group) for group in value]
    text = str(value or "").strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = (part.strip('"') for part in text.replace(",", " ").split())
    return [part for part in parts if part]

def required_role(route_key):
    """'GET /candidate/profile' -> 'candidate'. Routes without a role prefix -> None."""
    path = route_key.split(" ", 1)[-1]
    first_segment = path.strip("/").split("/", 1)[0]
    return first_segment if first_segment in ROLES else None

def authorize(event):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    groups = parse_groups(claims.get("cognito:groups"))
    roles = [role for role in ROLES if role in groups]
    if not roles:
        raise AccessDenied("No candidate or recruiter group")

    needed = required_role(event.get("routeKey", ""))
    if needed and needed not in roles:
        raise AccessDenied(f"Route needs {needed}")

    return {"user_id": claims["sub"], "role": needed or roles[0]}

def json_response(status_code, body):
    return{
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }

def api_handler(handler):
    """Wrap handler(event, user) -> (status_code, body) with the role check."""

    @functools.wraps(handler)
    def wrapper(event, context):
        try:
            user = authorize(event)
        except AccessDenied as error:
            print(f"Access denied on {event.get('routeKey')}: {error}")
            return json_response(403, {"message": "You don't have access to this."})

        try:
            status_code, body = handler(event, user)
            return json_response(status_code, body)
        except DatabaseStarting:
            return json_response(503, {"message": "KerjaReady is starting up. Try again in a moment."}) 
        except Exception:
            traceback.print_exc()
            return json_response(500, {"message": "Something went wrong. Try again."})

    return wrapper   