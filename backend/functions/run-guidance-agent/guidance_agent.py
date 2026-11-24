"""The guidance agent's model and limits (KR-97): Strands on Claude Haiku 5.5 in Amazon Bedrock.

Claude is not served in-Region in ap-southeast-5, so calls go through the global cross-Region inference profile,
which can process a request in any commercial AWS Region. The agent's tools must therefore return no resume text,
file names or personal details: only skill names, match types, ratings, posting counts and job posting lines.
"""

import os

from botocore.config import Config
from strands import Agent
from strands.hooks import BeforeInvocationEvent, BeforeToolCallEvent, HookProvider, HookRegistry
from strands.models import BedrockModel

MODEL_ID = "global.anthropic.claude-haiku-5-5"
MAX_TOOL_CALLS = 10
MAX_TOKENS = 8000
# One Bedrock call can wait for thinking and a long reply; the Lambda's own timeout bounds the whole run
BEDROCK_CONFIG = Config(read_timeout=120, retries={"max_attempts": 3, "mode": "standard"})


class ToolCallLimit(HookProvider):
    """Cancels every tool call after the first max_calls in one run. The model is told why, so it can finish.

    Strands returns structured output through a tool named after the output model; that call is never counted
    or cancelled, so a run that used all its tool calls can still return its output.
    """

    def __init__(self, output_tool, max_calls=MAX_TOOL_CALLS):
        self.output_tool = output_tool
        self.max_calls = max_calls
        self.calls = 0

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset)
        registry.add_callback(BeforeToolCallEvent, self.count)

    def reset(self, event: BeforeInvocationEvent) -> None:
        self.calls = 0

    def count(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] == self.output_tool:
            return
        self.calls += 1
        if self.calls > self.max_calls:
            event.cancel_tool = (
                f"Tool call limit reached: a run may make at most {self.max_calls} tool calls. "
                "Finish with the information you already have."
            )


def build_agent(system_prompt, tools, limit):
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=os.environ.get("AWS_REGION", "ap-southeast-5"),
        max_tokens=MAX_TOKENS,
        # Converse rather than ConverseStream: the run is in the background, and the role needs only
        # bedrock:InvokeModel
        streaming=False,
        boto_client_config=BEDROCK_CONFIG,
    )
    # No callback handler: the default one prints the model's text to the logs
    return Agent(model=model, system_prompt=system_prompt, tools=tools, hooks=[limit], callback_handler=None)


def run_agent(agent, prompt, output_model):
    """Returns (the output as a dict, input tokens, output tokens). Raises when no valid output comes back."""
    result = agent(prompt, structured_output_model=output_model)
    if result.structured_output is None:
        raise ValueError("The agent returned no structured output")
    usage = result.metrics.accumulated_usage
    return result.structured_output.model_dump(), usage.get("inputTokens"), usage.get("outputTokens")