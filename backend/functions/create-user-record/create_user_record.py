"""
Insert the users row for a newly confirmed account. 
Invoke asynchronously by the complete-registration lambda function. 
"""

import os
import time
import boto3
from botocore.exceptions import ClientError

rds_data = boto3.client("rds-data")
CLUSTER_ARN = os.environ["CLUSTER_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DATABASE_NAME = os.environ["DATABASE_NAME"]

MAX_ATTEMPTS = 24
RETRY_DELAY_SECONDS = 5

RECORD_FIELDS=(
    "user_id",
    "email",
    "full_name",
    "account_type",
    "company_name",
    "privacy_consented_at",
)

INSERT_USER_QUERY = """
INSERT INTO users (user_id, email, full_name, account_type, company_name, privacy_consented_at) 
VALUES (CAST(:user_id AS uuid), :email, :full_name, :account_type, :company_name, 
CAST(:privacy_consented_at AS timestamptz)) ON CONFLICT (user_id) DO NOTHING
"""

def to_parameter(name, value):
    if value is None:
        return {"name": name, "value": {"isNull": True}}
    return {"name": name, "value": {"stringValue": value}}

def handler(event, context):
    parameters = [to_parameter(field, event.get(field)) for field in RECORD_FIELDS]

    for attempt in range (1, MAX_ATTEMPTS + 1):
        try:
            rds_data.execute_statement(
                resourceArn=CLUSTER_ARN,
                secretArn=SECRET_ARN,
                database=DATABASE_NAME,
                sql=INSERT_USER_QUERY,
                parameters=parameters,
            )
            print(f"User record ready for {event['user_id']}")
            return
        except ClientError as error:
            is_resuming = error.response["Error"]["Code"] == "DatabaseResumingException"
            if not is_resuming or attempt == MAX_ATTEMPTS:
                raise
            print(f"Database resuming, retry {attempt} of {MAX_ATTEMPTS}")
            time.sleep(RETRY_DELAY_SECONDS)