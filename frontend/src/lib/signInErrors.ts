import {
  CODE_EXPIRED_MESSAGE,
  CODE_MISMATCH_MESSAGE,
  GENERIC_ERROR_MESSAGE,
  getErrorName,
  TOO_MANY_ATTEMPTS_MESSAGE,
} from "./cognitoMessages";
import { getPasswordRuleError, PASSWORD_HINT } from "./registrationValidation";

export type SignInErrorField = "code" | "password" | "form";

export type SignInError = {
  field: SignInErrorField;
  message: string;
};

// Maps a Sign In or password reset error (Amplify Auth / Cognito) to a message and the field it belongs to
export function mapSignInError(
  error: unknown,
  context: { password?: string } = {},
): SignInError {
  switch (getErrorName(error)) {
    case "NotAuthorizedException":
    case "UserNotFoundException":
      // Cognito locks an account for a while after repeated wrong passwords
      if (error instanceof Error && /attempts exceeded/i.test(error.message)) {
        return { field: "form", message: TOO_MANY_ATTEMPTS_MESSAGE };
      }
      return { field: "form", message: "Incorrect email or password." };
    case "LimitExceededException":
    case "TooManyRequestsException":
      return { field: "form", message: TOO_MANY_ATTEMPTS_MESSAGE };
    case "CodeMismatchException":
      return { field: "code", message: CODE_MISMATCH_MESSAGE };
    case "ExpiredCodeException":
      return { field: "code", message: CODE_EXPIRED_MESSAGE };
    case "InvalidPasswordException":
      return {
        field: "password",
        message: getPasswordRuleError(context.password ?? "") ?? PASSWORD_HINT,
      };
    default:
      return { field: "form", message: GENERIC_ERROR_MESSAGE };
  }
}
