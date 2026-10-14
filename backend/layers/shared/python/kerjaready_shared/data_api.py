"""
Run SQL through the RDS data API, waiting briefly while Aurora resumes from zero
"""

import json
import os
import time
import boto3
from botocore.exceptions import ClientError

# API Gateway gives up after 30s, so the total wait must be shorter than that
ATTEMPTS = 5
WAIT_SECONDS = 4

_rds_data = None

class DatabaseStarting(Exception):
    """Aurora is resume after scaling to zero"""

def _client():
    global _rds_data
    if _rds_data is None:
        _rds_data = boto3.client("rds-data")
    return _rds_data

def run_query(sql, parameters=None):
    """Return the rows as a list of dicts"""
    for attempt in range (1, ATTEMPTS+1):
        try:
            response = _client().execute_statement(
                resourceArn=os.environ["CLUSTER_ARN"],
                secretArn=os.environ["SECRET_ARN"],
                database=os.environ["DATABASE_NAME"],
                sql=sql,
                parameters=parameters or [],
                formatRecords="JSON",
            )
            return json.loads(response.get("formattedRecords") or "[]")

        except ClientError as error:
            if error.response["Error"]["Code"] != "DatabaseResumingException":
                raise
            if attempt == "ATTEMPTS":
                raise DatabaseStarting() from error
            time.sleep(WAIT_SECONDS)
