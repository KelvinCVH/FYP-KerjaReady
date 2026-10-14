"""
Cognito post confirmation trigger: Finish registration after the email is verified
"""

import json
import os
import boto3

cognito = boto3.client("cognito-idp")
lambda_client = boto3.client("lambda")

CREATE_USER_RECORD_FUNCTION_NAME = os.environ["CREATE_USER_RECORD_FUNCTION_NAME"]

def handler(event, context):
    if event["triggerSource"] != "PostConfirmation_ConfirmSignUp":
        print(f"Skipped trigger source: {event['triggerSource']}")
        return event # such as password reset

    user_pool_id = event["userPoolId"]
    username = event["userName"]
    attributes = event["request"]["userAttributes"]
    if "identities" in attributes or attributes.get("cognito:user_status") == "EXTERNAL_PROVIDER":
        account_type = "candidate"
    else:
        account_type = attributes["custom:account_type"]

    cognito.admin_add_user_to_group(
        UserPoolId=user_pool_id, Username=username, GroupName=account_type
    )

    # UserCreateDate is the consent time: email sign-ups must tick the consent box,
    # and Google users agree through the Privacy Notice line under the Google button.
    user = cognito.admin_get_user(UserPoolId=user_pool_id, Username=username)
    
    record = {
        "user_id": attributes["sub"],
        "email": attributes["email"].strip().lower(),
        "full_name": attributes["name"].strip(),
        "account_type": account_type,
        "company_name": (attributes.get("custom:company_name") or "").strip() or None,
        "privacy_consented_at": user["UserCreateDate"].isoformat(),
    }
    
    lambda_client.invoke(
        FunctionName=CREATE_USER_RECORD_FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps(record).encode("utf-8")
    )

    return event