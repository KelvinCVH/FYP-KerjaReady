import json

import pytest

from kerjaready_shared.api_handler import (
    AccessDenied,
    api_handler,
    authorize,
    parse_groups,
    required_role,
)


def make_event(route_key, groups):
    claims = {"sub": "11111111-1111-1111-1111-111111111111", "cognito:groups": groups}
    return {"routeKey": route_key, "requestContext": {"authorizer": {"jwt": {"claims": claims}}}}


@pytest.mark.parametrize(
    "value, expected",
    [
        ("[candidate]", ["candidate"]),
        ("[candidate ap-southeast-5_abc_Google]", ["candidate", "ap-southeast-5_abc_Google"]),
        ('["recruiter"]', ["recruiter"]),
        (["candidate"], ["candidate"]),
        (None, []),
    ],
)
def test_parse_groups(value, expected):
    assert parse_groups(value) == expected


def test_required_role():
    assert required_role("GET /candidate/profile") == "candidate"
    assert required_role("GET /recruiter/profile") == "recruiter"
    assert required_role("GET /health") is None


def test_candidate_can_use_candidate_route():
    assert authorize(make_event("GET /candidate/profile", "[candidate]"))["role"] == "candidate"


def test_candidate_blocked_from_recruiter_route():
    with pytest.raises(AccessDenied):
        authorize(make_event("GET /recruiter/profile", "[candidate]"))


def test_recruiter_blocked_from_candidate_route():
    with pytest.raises(AccessDenied):
        authorize(make_event("GET /candidate/profile", "[recruiter]"))


def test_google_group_is_ignored():
    event = make_event("GET /candidate/profile", "[ap-southeast-5_abc_Google candidate]")
    assert authorize(event)["role"] == "candidate"


def test_user_without_role_is_blocked():
    with pytest.raises(AccessDenied):
        authorize(make_event("GET /candidate/profile", "[ap-southeast-5_abc_Google]"))


def test_wrong_role_returns_json_403():
    @api_handler
    def handler(event, user):
        return 200, {"ok": True}

    response = handler(make_event("GET /recruiter/profile", "[candidate]"), None)

    assert response["statusCode"] == 403
    assert response["headers"]["Content-Type"] == "application/json"
    assert "message" in json.loads(response["body"])


def test_allowed_route_returns_json_body():
    @api_handler
    def handler(event, user):
        return 200, {"ok": True}

    response = handler(make_event("GET /candidate/profile", "[candidate]"), None)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert json.loads(response["body"]) == {"ok": True}