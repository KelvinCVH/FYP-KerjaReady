import { getPasswordRuleError, PASSWORD_HINT } from "./registrationValidation";

export type RegistrationErrorField = "email" | "password" | "code" | "form";

export type RegistrationError = {
  field: RegistrationErrorField;
  message: string;
  // Render a "Sign In" link after the message
  signInLink?: boolean;
};

const GENERIC_MESSAGE = "Something went wrong. Try again.";
const PRE_SIGN_UP_PREFIX = /^PreSignUp failed with error\s*/;

function getErrorName(error: unknown) {
  return error instanceof Error ? error.name : undefined;
}

// The pre sign-up Lambda's messages arrive as "PreSignUp failed with error <message>"
function cleanLambdaMessage(message: string) {
  const text = message.replace(PRE_SIGN_UP_PREFIX, "").trim().replace(/\.+$/, "");
  return text ? `${text}.` : GENERIC_MESSAGE;
}

// Maps an Amplify Auth (Cognito) error to a message and the field it belongs to
export function mapRegistrationError(
  error: unknown,
  context: { password?: string } = {},
): RegistrationError {
  switch (getErrorName(error)) {
    case "UsernameExistsException":
      return {
        field: "email",
        message: "An account with this email already exists.",
        signInLink: true,
      };
    case "InvalidPasswordException":
      return {
        field: "password",
        message: getPasswordRuleError(context.password ?? "") ?? PASSWORD_HINT,
      };
    case "UserLambdaValidationException":
      return { field: "form", message: cleanLambdaMessage((error as Error).message) };
    case "CodeMismatchException":
      return { field: "code", message: "That code is incorrect. Check the email and try again." };
    case "ExpiredCodeException":
      return {
        field: "code",
        message: "That code has expired. Select Resend Code to get a new one.",
      };
    case "LimitExceededException":
    case "TooManyRequestsException":
      return { field: "form", message: "Too many attempts. Wait a few minutes and try again." };
    default:
      return { field: "form", message: GENERIC_MESSAGE };
  }
}
