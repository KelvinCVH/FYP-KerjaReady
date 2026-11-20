"""Match the skills of every assessed resume again (KR-94).

Run it once after deploying skill matching, for resumes assessed before it existed, and again whenever the
matcher, the vocabulary or the semantic threshold changes. Each resume goes through kerjaready-process-resume
({"match_skills": <resume_id>}), which saves the skills; statuses and ratings do not change.

Usage (from the repo root):
    python scripts/rematch_resume_skills.py
"""

import argparse
import json
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

FUNCTION_NAME = "kerjaready-process-resume"
REGION = "ap-southeast-5"
DATABASE_WAITS = 6


def assessed_resume_ids(session, environment):
    """Ids of resumes with status done, waiting while Aurora resumes from zero."""
    rds_data = session.client("rds-data")
    for attempt in range(1, DATABASE_WAITS + 1):
        try:
            response = rds_data.execute_statement(
                resourceArn=environment["CLUSTER_ARN"],
                secretArn=environment["SECRET_ARN"],
                database=environment["DATABASE_NAME"],
                sql="SELECT resume_id FROM resumes WHERE status = 'done' ORDER BY resume_id",
                formatRecordsAs="JSON",
            )
            return [row["resume_id"] for row in json.loads(response.get("formattedRecords") or "[]")]
        except ClientError as error:
            if error.response["Error"]["Code"] != "DatabaseResumingException" or attempt == DATABASE_WAITS:
                raise
            print("Aurora is starting, waiting 10 s")
            time.sleep(10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="kerjaready")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=REGION)
    # Long enough for a cold assessment container. Never retried, so a resume is never matched twice at once.
    lambda_client = session.client("lambda", config=Config(read_timeout=120, retries={"total_max_attempts": 1}))
    environment = lambda_client.get_function_configuration(FunctionName=FUNCTION_NAME)["Environment"]["Variables"]

    resume_ids = assessed_resume_ids(session, environment)
    print(f"{len(resume_ids)} assessed resumes")
    failed = 0
    for resume_id in resume_ids:
        response = lambda_client.invoke(FunctionName=FUNCTION_NAME, Payload=json.dumps({"match_skills": resume_id}))
        body = json.loads(response["Payload"].read() or b"null")
        if response.get("FunctionError"):
            failed += 1
            print(f"resume {resume_id}: failed, {body.get('errorType') if isinstance(body, dict) else body}")
        else:
            print(f"resume {resume_id}: {body}")
    print(f"Finished: {len(resume_ids) - failed} matched, {failed} failed")


if __name__ == "__main__":
    main()