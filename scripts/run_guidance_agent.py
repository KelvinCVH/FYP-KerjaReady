"""Start one guidance agent run and wait for its result (KR-97).

The run is recorded in agent_runs like any other. The resume must be assessed (status done) and its owner must
have a target role. Use it to check the agent after a deploy (smoke_test) or to see a roadmap's output (roadmap).

Usage (from the repo root):
    python scripts/run_guidance_agent.py <resume_id>
    python scripts/run_guidance_agent.py <resume_id> --output-type roadmap
"""

import argparse
import json

import boto3
from botocore.config import Config

FUNCTION_NAME = "kerjaready-run-guidance-agent"
REGION = "ap-southeast-5"
# The function may run for up to 5 minutes; never retry, because a second call would start a second run
LAMBDA_CONFIG = Config(read_timeout=310, retries={"total_max_attempts": 1})


def main():
    parser = argparse.ArgumentParser(description="Run the guidance agent for one assessed resume.")
    parser.add_argument("resume_id", type=int)
    parser.add_argument("--output-type", default="smoke_test", choices=["smoke_test", "roadmap"])
    parser.add_argument("--profile", default="kerjaready")
    args = parser.parse_args()

    client = boto3.Session(profile_name=args.profile, region_name=REGION).client("lambda", config=LAMBDA_CONFIG)
    response = client.invoke(
        FunctionName=FUNCTION_NAME,
        Payload=json.dumps({"resume_id": args.resume_id, "output_type": args.output_type}),
    )
    result = json.loads(response["Payload"].read())
    if response.get("FunctionError"):
        print(f"The function failed: {result.get('errorType')}: {result.get('errorMessage')}")
        return
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()