"""An end-to-end check of the guidance agent on real data (KR-143, KR-144, KR-146): its tools and output.

The agent must choose which tools to call to answer, then return one structured result. It proves the model,
its permissions, the tools, the tool call limit and structured output all work before the roadmap prompt exists.

Each task module gives: PROMPT_VERSION, SYSTEM_PROMPT, make_tools(resume_id, role_id) and
prepare(resume_id, role_id), which returns the run's prompt and output model as a TaskRun. The tools are bound to
the run's resume and role, so the model can never ask about another candidate's data.
"""

import guidance_agent
import guidance_tools
from pydantic import BaseModel, Field

PROMPT_VERSION = "smoke-test-v3"
SYSTEM_PROMPT = (
    "You check that a career guidance service is working. Use the tools to look up the facts you need, and "
    "report only what they return. A skill that is not evidenced is one the resume does not show, not one the "
    "candidate lacks."
)
PROMPT = (
    "Find the candidate's target role, their lowest-rated assessment criterion and the three skills not "
    "evidenced in their resume that most postings ask for. Then say why the role asks for the first of "
    "those skills, citing the posting lines you used."
)


class OutputModel(BaseModel):
    """The smoke test's result."""

    role_title: str = Field(description="The candidate's target role")
    lowest_criterion: str = Field(description="The name of the lowest-rated assessment criterion")
    top_skills_not_evidenced: list[str] = Field(
        max_length=3, description="The three skills not evidenced in the resume that most postings ask for"
    )
    top_skill_reason: str = Field(description="Why the role asks for the first of those skills, in one sentence")
    source_posting_ids: list[int] = Field(description="The posting_id values of the posting lines that reason uses")
    summary: str = Field(description="One short sentence that states these facts")


def make_tools(resume_id, role_id):
    return guidance_tools.make_tools(resume_id, role_id)


def prepare(resume_id, role_id):
    return guidance_agent.TaskRun(PROMPT, OutputModel)