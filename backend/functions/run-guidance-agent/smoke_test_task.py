"""An end-to-end check of the guidance agent on real data (KR-143, KR-144): its tools and structured output.

The agent must choose which tools to call to answer, then return one structured result. It proves the model,
its permissions, the tools, the tool call limit and structured output all work before the roadmap prompt exists.

Each task module gives: PROMPT_VERSION, SYSTEM_PROMPT, OutputModel, make_tools(resume_id, role_id) and
build_prompt(). The tools are bound to the run's resume and role, so the model can never ask about another
candidate's data.
"""

import guidance_tools
from pydantic import BaseModel, Field

PROMPT_VERSION = "smoke-test-v2"
SYSTEM_PROMPT = (
    "You check that a career guidance service is working. Use the tools to look up the facts you need, and "
    "report only what they return. A skill that is not evidenced is one the resume does not show, not one the "
    "candidate lacks."
)


class OutputModel(BaseModel):
    """The smoke test's result."""

    role_title: str = Field(description="The candidate's target role")
    lowest_criterion: str = Field(description="The name of the lowest-rated assessment criterion")
    top_skills_not_evidenced: list[str] = Field(
        max_length=3, description="The three skills not evidenced in the resume that most postings ask for"
    )
    summary: str = Field(description="One short sentence that states these facts")


def make_tools(resume_id, role_id):
    return guidance_tools.make_tools(resume_id, role_id)


def build_prompt():
    return (
        "Find the candidate's target role, their lowest-rated assessment criterion and the three skills not "
        "evidenced in their resume that most postings ask for."
    )