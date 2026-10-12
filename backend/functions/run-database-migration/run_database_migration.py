"""
Apply the SQL migration files to Aurora through the RDS data API.
"""
import os
import time
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

rds_data = boto3.client("rds-data")

CLUSTER_ARN = os.environ["CLUSTER_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DATABASE_NAME = os.environ['DATABASE_NAME']

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
MAX_ATTEMPTS = 24
RETRY_DELAY_SECONDS = 5

def split_statements(sql_text: str) -> list[str]:
    """
    Split a migration file into single statements, skipping comment line.
    The Data API runs one statement per call, so each statement is sent seperately
    """
    statements, current = [], []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current))
            current = []
    if current:
        raise ValueError("The last statement does not end with a semicolon")
    
    return statements

def execute_statement(sql: str) -> None:
    """
    Run one statement, retrying while Aurora resumes from auto-pause
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            rds_data.execute_statement(
                resourceArn=CLUSTER_ARN,
                secretArn=SECRET_ARN,
                database=DATABASE_NAME,
                sql=sql,
            )
            return
        except ClientError as error:
            is_resuming = error.response["Error"]["Code"] == "DatabaseResumingException"
            if not is_resuming or attempt == MAX_ATTEMPTS:
                raise
            print(f"Database resuming, retry {attempt} of {MAX_ATTEMPTS}")
            time.sleep(RETRY_DELAY_SECONDS)

def handler(event, context):
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    statement_count = 0
    for migration_file in migration_files:
        for statement in split_statements(migration_file.read_text(encoding="utf-8")):
            try:
                execute_statement(statement)
            except ClientError as error:
                first_line = statement.splitlines()[0].strip()
                raise RuntimeError(
                    f"{migration_file.name} failed at: {first_line} | {error}"
                ) from error
            
            statement_count += 1
    print(f"Applied {statement_count} statements from {len(migration_files)} files")
    return {"files": len(migration_files), "statements": statement_count}
