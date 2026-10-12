"""Smoke test: confirm pgvector similarity search works through the Data API.

Runs inside a transaction that is rolled back, so no test data is left behind.
Usage (repo root, venv active): python scripts/test_vector_search.py
"""
import random
import time

import boto3
from botocore.exceptions import ClientError

STACK_NAME = "KerjaReadyStack"
DATABASE_NAME = "kerjaready"
EMBEDDING_DIMENSIONS = 1024

session = boto3.Session(profile_name="kerjaready", region_name="ap-southeast-5")
cloudformation = session.client("cloudformation")
rds_data = session.client("rds-data")


def get_stack_output(key: str) -> str:
    outputs = cloudformation.describe_stacks(StackName=STACK_NAME)["Stacks"][0]["Outputs"]
    return next(output["OutputValue"] for output in outputs if output["OutputKey"] == key)


CLUSTER_ARN = get_stack_output("ClusterArn")
SECRET_ARN = get_stack_output("SecretArn")


def begin_transaction() -> str:
    """Start a transaction, waiting while Aurora resumes from auto-pause."""
    for attempt in range(1, 25):
        try:
            return rds_data.begin_transaction(
                resourceArn=CLUSTER_ARN, secretArn=SECRET_ARN, database=DATABASE_NAME
            )["transactionId"]
        except ClientError as error:
            if error.response["Error"]["Code"] != "DatabaseResumingException":
                raise
            print(f"Database resuming, retry {attempt}")
            time.sleep(5)
    raise TimeoutError("Database did not resume in time")


def run(sql: str, transaction_id: str, parameters: list | None = None) -> dict:
    return rds_data.execute_statement(
        resourceArn=CLUSTER_ARN,
        secretArn=SECRET_ARN,
        database=DATABASE_NAME,
        transactionId=transaction_id,
        sql=sql,
        parameters=parameters or [],
    )


def to_vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in values) + "]"


def main() -> None:
    stored_embedding = [random.uniform(-1, 1) for _ in range(EMBEDDING_DIMENSIONS)]
    query_embedding = [value + random.uniform(-0.01, 0.01) for value in stored_embedding]

    transaction_id = begin_transaction()
    try:
        role_id = run(
            "INSERT INTO roles (title) VALUES ('Vector Test Role') RETURNING role_id;",
            transaction_id,
        )["records"][0][0]["longValue"]

        posting_id = run(
            "INSERT INTO job_postings (role_id, job_title) "
            "VALUES (:role_id, 'Vector Test Posting') RETURNING posting_id;",
            transaction_id,
            [{"name": "role_id", "value": {"longValue": role_id}}],
        )["records"][0][0]["longValue"]

        run(
            "INSERT INTO posting_chunks (posting_id, section_name, chunk_text, embedding) "
            "VALUES (:posting_id, 'requirements', 'Vector test chunk', CAST(:embedding AS vector));",
            transaction_id,
            [
                {"name": "posting_id", "value": {"longValue": posting_id}},
                {"name": "embedding", "value": {"stringValue": to_vector_literal(stored_embedding)}},
            ],
        )

        top_match = run(
            "SELECT chunk_text, 1 - (embedding <=> CAST(:query AS vector)) AS similarity "
            "FROM posting_chunks ORDER BY embedding <=> CAST(:query AS vector) LIMIT 1;",
            transaction_id,
            [{"name": "query", "value": {"stringValue": to_vector_literal(query_embedding)}}],
        )["records"][0]

        chunk_text = top_match[0]["stringValue"]
        similarity = top_match[1]["doubleValue"]
        print(f"Top match: {chunk_text} (cosine similarity {similarity:.4f})")

        if chunk_text == "Vector test chunk" and similarity > 0.99:
            print("PASS: vector search works")
        else:
            print("FAIL: unexpected search result")
    finally:
        rds_data.rollback_transaction(
            resourceArn=CLUSTER_ARN, secretArn=SECRET_ARN, transactionId=transaction_id
        )
        print("Transaction rolled back, no test data left")


if __name__ == "__main__":
    main()