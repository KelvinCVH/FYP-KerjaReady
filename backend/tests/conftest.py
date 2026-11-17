import importlib.util
from pathlib import Path

import pytest

FUNCTIONS_DIR = Path(__file__).resolve().parents[1] / "functions"
USER_ID = "11111111-1111-1111-1111-111111111111"


def load_function(folder_name):
    """Import a Lambda's module from backend/functions/<kebab-case folder>/<snake_case>.py."""
    module_name = folder_name.replace("-", "_")
    spec = importlib.util.spec_from_file_location(module_name, FUNCTIONS_DIR / folder_name / f"{module_name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate_event(route_key, resume_id):
    """An API Gateway event from a signed-in candidate, with {resume_id} in the path."""
    claims = {"sub": USER_ID, "cognito:groups": "[candidate]"}
    return {
        "routeKey": route_key,
        "pathParameters": {"resume_id": str(resume_id)},
        "requestContext": {"authorizer": {"jwt": {"claims": claims}}},
    }


def _plain(value):
    """A Data API parameter value as Python: {"isNull": True} -> None, {"longValue": 7} -> 7."""
    return None if value.get("isNull") else next(iter(value.values()))


class FakeDatabase:
    """Records each query. answer(sql, parameters) decides the rows each one returns."""

    def __init__(self, answer=None):
        self.queries = []
        self.answer = answer or (lambda sql, parameters: [])

    def __call__(self, sql, parameters=None):
        params = {item["name"]: _plain(item["value"]) for item in parameters or []}
        self.queries.append((sql, params))
        return self.answer(sql, params)

    def updates_of_status(self):
        return [(sql, params) for sql, params in self.queries if sql.startswith("UPDATE resumes SET status")]


@pytest.fixture
def fake_database():
    return FakeDatabase
