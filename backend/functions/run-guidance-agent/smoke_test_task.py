"""A small end-to-end check of the guidance agent (KR-143): one tool, one structured output.

It proves that the model, its permissions, the tool loop, the tool call limit and structured output all work
before the real tools and the roadmap prompt exist. It uses only knowledge base data, never resume text or
personal details.

Each task module gives: PROMPT_VERSION, SYSTEM_PROMPT, OutputModel, make_tools(resume_id, role_id) and
build_prompt(). The tools are bound to the run's resume and role, so the model can never ask about another
candidate's data.
"""

from kerjaready_shared.data_api import run_query
from pydantic import BaseModel, Field
from strands import tool

PROMPT_VERSION = "smoke-test-v1"
SYSTEM_PROMPT = (
    "You check that a career guidance service is working. Use the tool to look up the facts you need. "
    "Report only what the tool returns."
)

ROLE_PROFILE_SIZE = """
SELECT ro.title, count(rq.skill_id) AS skills
FROM roles ro
LEFT JOIN role_skills rq ON rq.role_id = ro.role_id
WHERE ro.role_id = :role_id
GROUP BY ro.title
"""


class OutputModel(BaseModel):
    """The smoke test's result."""

    role_title: str = Field(description="The target role title the tool returned")
    skill_count: int = Field(description="How many skills the tool says the role profile lists")
    summary: str = Field(description="One short sentence that states both facts")


def make_tools(resume_id, role_id):
    @tool
    def get_target_role_profile() -> str:
        """Look up the candidate's target role: its title and how many skills its profile lists."""
        rows = run_query(ROLE_PROFILE_SIZE, [{"name": "role_id", "value": {"longValue": role_id}}])
        if not rows:
            return "The target role was not found."
        return f"{rows[0]['title']}: {rows[0]['skills']} skills in its profile"

    return [get_target_role_profile]


def build_prompt():
    return "Look up the target role, then report its title and how many skills its profile lists."