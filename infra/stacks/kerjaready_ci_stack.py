"""
Use Github Actions deploy KerjaReadyStack without stored AWS key
"""

from aws_cdk import (
    CfnOutput, 
    Duration, 
    Stack, 
    aws_iam as iam,
)
from constructs import Construct

GITHUB_MAIN_BRANCH_SUBJECT = "repo:KelvinCVH@139412913/FYP-KerjaReady@1405526635:ref:refs/heads/main"

class KerjaReadyCiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Github proves who it is with a short-lived token, so no AWS keys are stored
        github_provider = iam.OpenIdConnectProvider(
            self,
            "GithubOidcProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        # Only the main branch of this repo can take this role
        deploy_role = iam.Role(
            self,
            "GitHubDeployRole",
            role_name="kerjaready-github-deploy",
            description="Assumed by Github Actions on main to run cdk deploy",
            max_session_duration=Duration.hours(1),
            assumed_by=iam.WebIdentityPrincipal(
                github_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                        "token.actions.githubusercontent.com:sub": GITHUB_MAIN_BRANCH_SUBJECT,
                    }
                },
            ),
        )

        # It can only use the CDK bootstrap roles to do actual deployment
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-hnb659fds-*"],
            )
        )

        CfnOutput(self, "GitHubDeployRoleArn", value=deploy_role.role_arn)