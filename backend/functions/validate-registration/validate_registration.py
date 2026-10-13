"""
Cognito pre sign-up trigger: Validate a registration before Cognito creates the users.
Cognito shows errors raised here as "PreSignUp failed with error <message>"
"""

ACCOUNT_TYPES = {"candidate", "recruiter"}

def handler(event, context):
    if event["triggerSource"] != "PreSignUp_SignUp":
        # Only self registration is supported. This will be updated in KR-74 (Google OAuth sign up)
        raise ValueError("This registration method is not supported")

    attributes = event["request"]["userAttributes"]
    validation_data = event["request"].get("validationData") or {}

    if validation_data.get("privacy_consent") != "true":
        raise ValueError("You must agree to the Privacy Notice to create an account")

    account_type = attributes.get("custom:account_type")
    if account_type not in ACCOUNT_TYPES:
        raise ValueError("Please choose whether you are candidate or recruiter")

    if not attributes.get("name", "").strip():
        raise ValueError("Please enter your full name")

    company_name = attributes.get("custom:company_name", "").strip()
    if account_type == "recruiter" and not company_name:
        raise ValueError("Please enter your company name")
    if account_type == "candidate" and company_name:
        raise ValueError("Company name applies to recruiter account only")

    return event