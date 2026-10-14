from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    SecretValue,
    triggers,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
)

from constructs import Construct

PG_VERSION = "16.14"
GOOGLE_CLIENT_ID = "652526367677-cuaork6oth7a82vdcuat7dqgac9l7cal.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET_NAME = "kerjaready-google-client-secret"
WEB_APP_URLS = ["http://localhost:5173"]
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

        # Shared settings for every Lambda that uses the Data API
        data_api_environment = {
            "CLUSTER_ARN": self.cluster.cluster_arn,
            "SECRET_ARN": self.cluster.secret.secret_arn,
            "DATABASE_NAME": DATABASE_NAME,
        }

        # Registration: Lambda function used by Cognito triggers
        create_user_record_function = self._create_python_function(
            "CreateUserRecordFunction",
            "create-user-record",
            timeout=Duration.minutes(3),
            environment=data_api_environment,
        )
        self.cluster.grant_data_api_access(create_user_record_function)

        validate_registration_function = self._create_python_function(
            "ValidateRegistrationFunction",
            "validate-registration",
            timeout=Duration.seconds(5),
            memory_size=512,
        )

        complete_registration_function = self._create_python_function(
            "CompleteRegistrationFunction",
            "complete-registration",
            timeout=Duration.seconds(5),
            memory_size=512,
            environment={
                "CREATE_USER_RECORD_FUNCTION_NAME": create_user_record_function.function_name,
            },
        )
        create_user_record_function.grant_invoke(complete_registration_function)

        # A wildcard pool ARN avoids a circular dependency between the pool and its own trigger
        complete_registration_function.add_to_role_policy(
            iam.PolicyStatement(
                actions = ["cognito-idp:AdminAddUserToGroup", "cognito-idp:AdminGetUser"],
                resources=[
                    self.format_arn(service="cognito-idp", resource="userpool",resource_name="*")
                ],
            )
        )

        validate_registration_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cognito-idp:ListUsers", "cognito-idp:AdminLinkProviderForUser"],
                resources=[
                    self.format_arn(service="cognito-idp", resource="userpool", resource_name="*")
                ],
            )
        )

        # Auth: Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            "KerjaReadyUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            sign_in_case_sensitive=False,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            keep_original=cognito.KeepOriginalAttrs(email=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                fullname=cognito.StandardAttribute(required=True, mutable=True),
            ),
            custom_attributes={
                "account_type": cognito.StringAttribute(min_len=1, max_len=20, mutable=False),
                "company_name": cognito.StringAttribute(min_len=1, max_len=150, mutable=True),
            },
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            user_verification=cognito.UserVerificationConfig(
                email_style=cognito.VerificationEmailStyle.CODE,
                email_subject="Your KerjaReady verification code",
                email_body="Your KerjaReady verification code is {####}. Enter it to finish creating your account",
            ),
            lambda_triggers=cognito.UserPoolTriggers(
                pre_sign_up=validate_registration_function,
                post_confirmation=complete_registration_function,
            ),
        )

        # Cognito domain for Google sign-in redirects
        self.user_pool_domain = self.user_pool.add_domain(
            "KerjaReadyUserPoolDomain",
            cognito_domain = cognito.CognitoDomainOptions(domain_prefix="kerjaready"),
        )

        # Google sign-in
        google_provider = cognito.UserPoolIdentityProviderGoogle(
            self,
            "GoogleIdentityProvider",
            user_pool = self.user_pool,
            client_id = GOOGLE_CLIENT_ID,
            client_secret_value = SecretValue.secrets_manager(GOOGLE_CLIENT_SECRET_NAME),
            scopes=["openid","email","profile"],
            attribute_mapping=cognito.AttributeMapping(
                email=cognito.ProviderAttribute.GOOGLE_EMAIL,
                email_verified=cognito.ProviderAttribute.GOOGLE_EMAIL_VERIFIED,
                fullname=cognito.ProviderAttribute.GOOGLE_NAME,
            )
        )

        client_read_attributes = (
            cognito.ClientAttributes()
            .with_standard_attributes(email=True, email_verified=True, fullname=True)
            .with_custom_attributes("account_type", "company_name")
        )
        client_write_attributes = (
            cognito.ClientAttributes()
            .with_standard_attributes(email=True, fullname=True)
            .with_custom_attributes("account_type", "company_name")
        )

        self.user_pool_client = self.user_pool.add_client(
            "WebClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[f"{url}/auth/callback" for url in WEB_APP_URLS],
                logout_urls=[f"{url}/sign-in" for url in WEB_APP_URLS],
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO,
                cognito.UserPoolClientIdentityProvider.GOOGLE,
            ],
            prevent_user_existence_errors=True,
            read_attributes=client_read_attributes,
            write_attributes=client_write_attributes,
        )
        self.user_pool_client.node.add_dependency(google_provider)

        for group in ("candidate", "recruiter"):
            cognito.CfnUserPoolGroup(
                self,
                f"{group.capitalize()}Group",
                user_pool_id=self.user_pool.user_pool_id,
                group_name=group,
            )

        # Lambda: health check through the Data API
        check_health_function = self._create_python_function(
            "CheckHealthFunction",
            "check-health",
            timeout=Duration.seconds(25),
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
        run_database_migration_function = self._create_python_function(
            "RunDatabaseMigrationFunction",
            "run-database-migration",
            timeout=Duration.minutes(4),
            environment=data_api_environment,
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
        CfnOutput(self, "UserPoolDomainUrl", value=self.user_pool_domain.base_url())
        CfnOutput(self, "GoogleRedirectUrl", value=f"{self.user_pool_domain.base_url()}/oauth2/idpresponse",)
        CfnOutput(self, "ApiUrl", value=self.http_api.api_endpoint)

    def _create_python_function(
        self,
        construct_id: str,
        folder_name: str,
        timeout: Duration,
        environment: dict | None=None,
        memory_size: int=256,
    ) -> _lambda.Function:
        """Creata a Python 3.12 Lambda from backend/functions/"""
        module_name= folder_name.replace("-", "_")
        return _lambda.Function(
            self, 
            construct_id,
            function_name = f"kerjaready-{folder_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler=f"{module_name}.handler",
            code=_lambda.Code.from_asset(str(FUNCTIONS_DIR / folder_name)),
            timeout=timeout,
            memory_size=memory_size,
            environment=environment or {},
        )