import json
import os
import time
import boto3
from botocore.exceptions import ClientError

rds_data = boto3.client("rds-data")

CLUSTER_ARN = os.environ["CLUSTER_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DATABASE_NAME = os.environ["DATABASE_NAME"]
MAX_ATTEMPTS = 5
RETRY_DELAY_SECONDS = 4

def get_database_version() -> str:
    """Query the database version, retrying while Aurora resumes from auto-pause"""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = rds_data.execute_statement(
                resourceArn=CLUSTER_ARN,
                secretArn=SECRET_ARN,
                database=DATABASE_NAME,
                sql="SELECT version();",
            )
            return result ["records"][0][0]["stringValue"]
        except ClientError as error:
            is_resuming = error.response["Error"]["Code"] == "DatabaseResumingException"
            if not is_resuming or attempt == MAX_ATTEMPTS:
                raise
            time.sleep(RETRY_DELAY_SECONDS)

def handler(event, context):
    try:
        body = {"status": "ok", "database": get_database_version()}
        status_code = 200
    except Exception as e:
        body = {"status": "unavailable", "error": type(error).__name__}
        status_code = 503

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }