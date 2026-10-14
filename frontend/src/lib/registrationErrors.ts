import {
  cleanCognitoMessage,
  CODE_EXPIRED_MESSAGE,
  CODE_MISMATCH_MESSAGE,
  GENERIC_ERROR_MESSAGE,
  getErrorName,
  TOO_MANY_ATTEMPTS_MESSAGE,
} from "./cognitoMessages";
import { getPasswordRuleError, PASSWORD_HINT } from "./registrationValidation";

export type RegistrationErrorField = "email" | "password" | "code" | "form";

export type RegistrationError = {
  field: RegistrationErrorField;
  message: string;
  // Render a "Sign In" link after the message
  signInLink?: boolean;
};

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
      return { field: "form", message: cleanCognitoMessage((error as Error).message) };
    case "CodeMismatchException":
      return { field: "code", message: CODE_MISMATCH_MESSAGE };
    case "ExpiredCodeException":
      return { field: "code", message: CODE_EXPIRED_MESSAGE };
    case "LimitExceededException":
    case "TooManyRequestsException":
      return { field: "form", message: TOO_MANY_ATTEMPTS_MESSAGE };
    default:
      return { field: "form", message: GENERIC_ERROR_MESSAGE };
  }
}
