"""
Pre sign-up trigger: checks new email accounts and links Google sign-ins to verified accounts.
Cognito shows errors raised here as "PreSignUp failed with error <message>"
"""
import boto3
cognito = boto3.client("cognito-idp")

ACCOUNT_TYPES = {"candidate", "recruiter"}
GOOGLE_PROVIDER_NAME = "Google"

def handler(event, context):
    trigger_source = event["triggerSource"]

    if trigger_source == "PreSignUp_SignUp":
        validate_email_sign_up(event)
    elif trigger_source == "PreSignUp_ExternalProvider":
        link_google_to_existing_account(event)
    else:
        raise Exception("This registration method is not supported.")

    return event

def validate_email_sign_up(event):
    attributes = event["request"].get("userAttributes", {})
    validation_data = event["request"].get("validationData") or {}

    if validation_data.get("privacy_consent") != "true":
        raise Exception("You must agree to the Privacy Notice to create an account.")

    account_type = attributes.get("custom:account_type")
    if account_type not in ACCOUNT_TYPES:
        raise Exception("Please choose whether you are a candidate or a recruiter.")

    if not attributes.get("name", "").strip():
        raise Exception("Please enter your full name.")

    company_name = attributes.get("custom:company_name", "").strip()
    if account_type == "recruiter" and not company_name:
        raise Exception("Please enter your company name.")
    if account_type == "candidate" and company_name:
        raise Exception("Company name applies to recruiter accounts only.")

def link_google_to_existing_account(event):
    attributes = event["request"].get("userAttributes", {})
    print(f"Google attribute names: {sorted(attributes)}")

    if attributes.get("email_verified") != "true":
        raise Exception("Your Google email is not verified. Create an account with your email instead.")

    email = attributes.get("email", "").strip().lower()
    existing_user = find_email_account(event["userPoolId"], email)

    if existing_user is None:
        return # New Google user, complete registration makes them a candidate

    if (
        existing_user["UserStatus"] != "CONFIRMED"
        or get_attribute(existing_user, "email_verified") != "true"
    ):
        raise Exception("Verify your email to finish creating your account, then continue with Google.")

    google_user_id = event["userName"].split("_", 1)[1]
    cognito.admin_link_provider_for_user(
        UserPoolId=event["userPoolId"],
        DestinationUser={
            "ProviderName": "Cognito",
            "ProviderAttributeValue": existing_user["Username"],
        },
        SourceUser={
            "ProviderName": GOOGLE_PROVIDER_NAME,
            "ProviderAttributeName": "Cognito_Subject",
            "ProviderAttributeValue": google_user_id,
        },
    )
    print(f"Linked Google sign-in to existing user {existing_user['Username']}")

def find_email_account(user_pool_id, email):
    """Return the email and password for this email, or None"""
    response = cognito.list_users(UserPoolId=user_pool_id, Filter=f'email = "{email}"')
    for user in response["Users"]:
        if user["UserStatus"] != "EXTERNAL_PROVIDER":
            return user
    return None

def get_attribute(user, name):
    for attribute in user.get("Attributes", []):
        if attribute["Name"] == name:
            return attribute["Value"]
    return None

