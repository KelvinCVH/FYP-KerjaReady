"""Delete every resume, to start testing again from no resumes.

Deletes every row in resumes, and with it (ON DELETE CASCADE) each resume's ratings, matched skills,
assessments, match results and applications. Then deletes every PDF under resumes/ in the resume bucket.
Accounts, profiles and target roles are kept. This cannot be undone.

Usage (from the repo root):
    python scripts/delete_all_resumes.py            # dry run: shows what would be deleted
    python scripts/delete_all_resumes.py --delete   # deletes, after you type DELETE
"""

import argparse
import json
import time

import boto3
from botocore.exceptions import ClientError

REGION = "ap-southeast-5"
STACK_NAME = "KerjaReadyStack"
# Any Lambda with the Data API settings will do; this one already serves rematch_resume_skills.py
DATABASE_FUNCTION = "kerjaready-process-resume"
RESUME_PREFIX = "resumes/"
DATABASE_WAITS = 6
S3_BATCH = 1000

COUNTS = """
SELECT (SELECT count(*) FROM resumes) AS resumes,
       (SELECT count(*) FROM resume_ratings) AS ratings,
       (SELECT count(*) FROM resume_skills) AS matched_skills,
       (SELECT count(*) FROM assessments) AS assessments,
       (SELECT count(*) FROM match_results) AS match_results,
       (SELECT count(*) FROM applications) AS applications
"""


def run_sql(rds_data, environment, sql):
    """Runs one statement, waiting while Aurora resumes from zero."""
    for attempt in range(1, DATABASE_WAITS + 1):
        try:
            return rds_data.execute_statement(
                resourceArn=environment["CLUSTER_ARN"],
                secretArn=environment["SECRET_ARN"],
                database=environment["DATABASE_NAME"],
                sql=sql,
                formatRecordsAs="JSON",
            )
        except ClientError as error:
            if error.response["Error"]["Code"] != "DatabaseResumingException" or attempt == DATABASE_WAITS:
                raise
            print("Aurora is starting, waiting 10 s")
            time.sleep(10)


def resume_bucket_name(session):
    stack = session.client("cloudformation").describe_stacks(StackName=STACK_NAME)["Stacks"][0]
    for output in stack.get("Outputs", []):
        if output["OutputKey"] == "ResumeBucketName":
            return output["OutputValue"]
    raise SystemExit(f"{STACK_NAME} has no ResumeBucketName output")


def resume_object_keys(s3, bucket):
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=RESUME_PREFIX):
        keys.extend(item["Key"] for item in page.get("Contents", []))
    return keys


def delete_objects(s3, bucket, keys):
    """Deletes the keys in batches of 1000 and returns how many were deleted."""
    deleted = 0
    for start in range(0, len(keys), S3_BATCH):
        batch = keys[start:start + S3_BATCH]
        response = s3.delete_objects(
            Bucket=bucket, Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True}
        )
        errors = response.get("Errors", [])
        for error in errors:
            print(f"Could not delete {error['Key']}: {error['Code']}")
        deleted += len(batch) - len(errors)
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Delete every resume and its PDF.")
    parser.add_argument("--profile", default="kerjaready")
    parser.add_argument("--delete", action="store_true", help="delete; without it, only show what would go")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=REGION)
    environment = session.client("lambda").get_function_configuration(FunctionName=DATABASE_FUNCTION)[
        "Environment"
    ]["Variables"]
    rds_data = session.client("rds-data")
    s3 = session.client("s3")
    bucket = resume_bucket_name(session)

    counts = json.loads(run_sql(rds_data, environment, COUNTS).get("formattedRecords") or "[{}]")[0]
    keys = resume_object_keys(s3, bucket)
    print("Would delete:" if not args.delete else "Will delete:")
    for name, count in counts.items():
        print(f"  {name}: {count}")
    print(f"  PDFs in s3://{bucket}/{RESUME_PREFIX}: {len(keys)}")

    if not args.delete:
        print("Dry run: nothing was deleted. Run again with --delete to delete.")
        return
    if input("This cannot be undone. Type DELETE to continue: ").strip() != "DELETE":
        print("Cancelled: nothing was deleted.")
        return

    # Rows first: if the PDFs then fail, a rerun finds and deletes them, and no row points at a missing file
    deleted_rows = run_sql(rds_data, environment, "DELETE FROM resumes").get("numberOfRecordsUpdated", 0)
    print(f"Deleted {deleted_rows} resumes and their linked rows")
    # Listed again, so a PDF uploaded since the count goes too
    deleted_files = delete_objects(s3, bucket, resume_object_keys(s3, bucket))
    print(f"Deleted {deleted_files} PDFs")


if __name__ == "__main__":
    main()