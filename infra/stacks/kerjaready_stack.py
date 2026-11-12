from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    SecretValue,
    Annotations,
    triggers,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_apigatewayv2_authorizers as apigwv2_authorizers,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_ecr_assets as ecr_assets,
)

from constructs import Construct

PG_VERSION = "16.14"
GOOGLE_CLIENT_ID = "652526367677-cuaork6oth7a82vdcuat7dqgac9l7cal.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET_NAME = "kerjaready-google-client-secret"
WEB_APP_URLS = ["http://localhost:5173"]
DATABASE_NAME = "kerjaready"
FUNCTIONS_DIR = Path(__file__).resolve().parents[2] / "backend" / "functions"
LAYERS_DIR = Path(__file__).resolve().parents[2] / "backend" / "layers"
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

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

        self.frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
        )

        self.frontend_distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            comment="kerjaready-frontend",
            default_root_object="index.html",
            price_class=cloudfront.PriceClass.PRICE_CLASS_200,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.frontend_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
            ),
            # React router handles every path, unknown files fall back to index.html
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=status,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                )
                for status in (403, 404)
            ],
        )

        frontend_url = f"https://{self.frontend_distribution.distribution_domain_name}"
        web_app_urls = [*WEB_APP_URLS, frontend_url]

        # Upload the built frontend and clear CloudFront's cache
        if (FRONTEND_DIST / "index.html").exists():
            s3deploy.BucketDeployment(
                self,
                "FrontendDeployment",
                sources=[s3deploy.Source.asset(str(FRONTEND_DIST))],
                destination_bucket=self.frontend_bucket,
                distribution=self.frontend_distribution,
                distribution_paths=["/*"],
                memory_limit=512,
            )
        else:
            Annotations.of(self).add_warning(
                "frontend/dist not found. Run npm run build in frontend before cdk deploy."
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
                callback_urls=[f"{url}/auth/callback" for url in web_app_urls],
                logout_urls=[f"{url}/sign-in" for url in web_app_urls],
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

        shared_layer = _lambda.LayerVersion(
            self,
            "SharedCodeLayer",
            layer_version_name="kerjaready-shared",
            code=_lambda.Code.from_asset(str(LAYERS_DIR/ "shared")),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Shared API role checks and Data API helper",
        )

        # API: every route requires a Cognito sign-in by default
        user_pool_authorizer = apigwv2_authorizers.HttpUserPoolAuthorizer(
            "CognitoUserPoolAuthorizer",
            self.user_pool,
            user_pool_clients=[self.user_pool_client],
        )

        self.http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name="kerjaready-api",
            default_authorizer=user_pool_authorizer,
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=web_app_urls,
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.PUT,
                    apigwv2.CorsHttpMethod.DELETE,
                ],
                allow_headers=["authorization", "content-type"],
                max_age=Duration.days(1),
            ),
        )

        # Public: health check only
        self.http_api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integrations.HttpLambdaIntegration(
                "CheckHealthIntegration", check_health_function
            ),
            authorizer=apigwv2.HttpNoneAuthorizer(),
        )

        # Signed In: Each user's own profile, checked by role in the shared layer
        get_user_profile_function = self._create_python_function(
            "GetUserProfileFunction",
            "get-user-profile",
            timeout=Duration.seconds(29),
            environment=data_api_environment,
            layers=[shared_layer],
        )
        self.cluster.grant_data_api_access(get_user_profile_function)

        profile_integration = apigwv2_integrations.HttpLambdaIntegration(
            "GetUserProfileIntegration", get_user_profile_function
        )

        for role in ("candidate", "recruiter"):
            self.http_api.add_routes(
                path=f"/{role}/profile",
                methods=[apigwv2.HttpMethod.GET],
                integration=profile_integration,
            )

        # Signed-in: KB roles for the role picker
        list_roles_function = self._create_python_function(
            "ListRolesFunction",
            "list-roles",
            timeout=Duration.seconds(29),
            environment=data_api_environment,
            layers=[shared_layer],
        )
        self.cluster.grant_data_api_access(list_roles_function)
        self.http_api.add_routes(
            path="/roles",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integrations.HttpLambdaIntegration("ListRolesIntegration", list_roles_function),
        )

        # Candidate: save or clear the target role
        save_target_role_function = self._create_python_function(
            "SaveTargetRoleFunction",
            "save-target-role",
            timeout=Duration.seconds(29),
            environment=data_api_environment,
            layers=[shared_layer],
        )
        self.cluster.grant_data_api_access(save_target_role_function)
        self.http_api.add_routes(
            path="/candidate/target-role",
            methods=[apigwv2.HttpMethod.PUT],
            integration=apigwv2_integrations.HttpLambdaIntegration("SaveTargetRoleIntegration", save_target_role_function),
        )

        # Resume assessment: ONNX rating model and LanguagueTool in one container image
        # Model files are saved in S3 
        assess_resume_function = _lambda.DockerImageFunction(
            self,
            "AssessResumeFunction",
            function_name="kerjaready-assess-resume",
            code=_lambda.DockerImageCode.from_image_asset(
                str(FUNCTIONS_DIR / "assess-resume"),
                platform=ecr_assets.Platform.LINUX_AMD64,
            ),
            memory_size=3008,
            timeout=Duration.seconds(120),
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
        CfnOutput(self, "FrontendUrl", value=frontend_url)

    def _create_python_function(
        self,
        construct_id: str,
        folder_name: str,
        timeout: Duration,
        environment: dict | None=None,
        memory_size: int=256,
        layers: list | None = None,
    ) -> _lambda.Function:
        """Create a Python 3.12 Lambda from backend/functions/"""
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
            layers=layers or [],
        )