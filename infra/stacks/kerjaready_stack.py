from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    triggers,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_cognito as cognito,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
)

from constructs import Construct

PG_VERSION = "16.14"
DATABASE_NAME = "kerjaready"
FUNCTIONS_DIR = Path(__file__).resolve().parents[2] / "backend" / "functions"

class KerjaReadyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Network: isolated subnets for Aurora only, no NAT gateway
        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="db",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                )
            ],
        )

        # Database: Aurora Serverless v2 PostgreSQL with Data API
        self.cluster = rds.DatabaseCluster(
            self,
            "Database",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.of(PG_VERSION, "16")),
            writer=rds.ClusterInstance.serverless_v2("writer"),
            serverless_v2_min_capacity=0,
            serverless_v2_max_capacity=2,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            credentials=rds.Credentials.from_generated_secret("kr_admin"),
            default_database_name=DATABASE_NAME,
            enable_data_api=True,
            storage_encrypted=True,
        )

        # Storage: private resume bucket
        self.resume_bucket = s3.Bucket(
            self,
            "ResumeBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
        )

        # Auth: Cognito User Pool, web client, role groups
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
        )
        self.user_pool_client = self.user_pool.add_client(
            "WebClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_srp=True),
            disable_o_auth=True,
        )
        for group in ("candidate", "recruiter"):
            cognito.CfnUserPoolGroup(
                self,
                f"{group.capitalize()}Group",
                user_pool_id=self.user_pool.user_pool_id,
                group_name=group,
            )

        # Shared settings for every Lambda that uses the Data API
        data_api_environment = {
            "CLUSTER_ARN": self.cluster.cluster_arn,
            "SECRET_ARN": self.cluster.secret.secret_arn,
            "DATABASE_NAME": DATABASE_NAME,
        }

        # Lambda: health check through the Data API
        check_health_function = _lambda.Function(
            self,
            "CheckHealthFunction",
            function_name="kerjaready-check-health",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="check_health.handler",
            code=_lambda.Code.from_asset(str(FUNCTIONS_DIR / "check-health")),
            timeout=Duration.seconds(25),
            memory_size=256,
            environment=data_api_environment,
        )
        self.cluster.grant_data_api_access(check_health_function)

        # API: HTTP API with a public health route
        self.http_api = apigwv2.HttpApi(self, "HttpApi", api_name="kerjaready-api")
        self.http_api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integrations.HttpLambdaIntegration(
                "CheckHealthIntegration", check_health_function
            ),
        )

        # Lambda: Apply SQL migrations through the Data API
        run_database_migration_function = _lambda.Function(
            self,
            "RunDatabaseMigrationFunction",
            function_name = "kerjaready-run-database-migration",
            runtime = _lambda.Runtime.PYTHON_3_12,
            handler = "run_database_migration.handler",
            code = _lambda.Code.from_asset(str(FUNCTIONS_DIR / "run-database-migration")),
            timeout = Duration.minutes(4),
            memory_size = 256,
            environment = data_api_environment,
        )
        self.cluster.grant_data_api_access(run_database_migration_function)

        # Trigger: run the migration during deploy, after the cluster exists
        triggers.Trigger(
            self,
            "RunDatabaseMigrationTrigger",
            handler = run_database_migration_function,
            timeout = Duration.minutes(5),
            execute_after=[self.cluster],
        )

        # Outputs used by later components and the frontend
        CfnOutput(self, "ClusterArn", value=self.cluster.cluster_arn)
        CfnOutput(self, "SecretArn", value=self.cluster.secret.secret_arn)
        CfnOutput(self, "ResumeBucketName", value=self.resume_bucket.bucket_name)
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
        CfnOutput(self, "ApiUrl", value=self.http_api.api_endpoint)