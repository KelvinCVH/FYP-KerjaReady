import boto3
import pytest
from botocore.stub import Stubber

from kerjaready_shared import data_api
from kerjaready_shared.data_api import DatabaseStarting, run_query

CLUSTER_ARN = "arn:aws:rds:ap-southeast-5:123456789012:cluster:kerjaready-test"
SECRET_ARN = "arn:aws:secretsmanager:ap-southeast-5:123456789012:secret:kerjaready-test"
SQL = "SELECT email FROM users WHERE user_id = CAST(:user_id AS uuid)"
PARAMETERS = [{"name": "user_id", "value": {"stringValue": "11111111-1111-1111-1111-111111111111"}}]


@pytest.fixture
def rds_data(monkeypatch):
    """A stubbed rds-data client in place of the real one. Nothing reaches AWS."""
    monkeypatch.setenv("CLUSTER_ARN", CLUSTER_ARN)
    monkeypatch.setenv("SECRET_ARN", SECRET_ARN)
    monkeypatch.setenv("DATABASE_NAME", "kerjaready")
    client = boto3.client(
        "rds-data",
        region_name="ap-southeast-5",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    monkeypatch.setattr(data_api, "_rds_data", client)
    with Stubber(client) as stubber:
        yield stubber


def test_execute_statement_parameters_match_the_api(rds_data):
    # botocore validates the call against the real rds-data model, so an unknown parameter fails here
    rds_data.add_response(
        "execute_statement",
        {"formattedRecords": '[{"email": "nurul.aina@example.com"}]'},
        expected_params={
            "resourceArn": CLUSTER_ARN,
            "secretArn": SECRET_ARN,
            "database": "kerjaready",
            "sql": SQL,
            "parameters": PARAMETERS,
            "formatRecordsAs": "JSON",
        },
    )

    assert run_query(SQL, PARAMETERS) == [{"email": "nurul.aina@example.com"}]
    rds_data.assert_no_pending_responses()


def test_database_still_resuming_raises_database_starting(rds_data, monkeypatch):
    sleeps = []
    monkeypatch.setattr(data_api.time, "sleep", sleeps.append)
    for _ in range(data_api.ATTEMPTS):
        rds_data.add_client_error(
            "execute_statement",
            service_error_code="DatabaseResumingException",
            http_status_code=400,
        )

    with pytest.raises(DatabaseStarting):
        run_query(SQL, PARAMETERS)

    # Every attempt was used, with a wait between each one
    rds_data.assert_no_pending_responses()
    assert sleeps == [data_api.WAIT_SECONDS] * (data_api.ATTEMPTS - 1)
