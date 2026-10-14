// Messages shared by the Create Account, Sign In and password reset error mappers

export const GENERIC_ERROR_MESSAGE = "Something went wrong. Try again.";
export const TOO_MANY_ATTEMPTS_MESSAGE = "Too many attempts. Wait a few minutes and try again.";
export const CODE_MISMATCH_MESSAGE = "That code is incorrect. Check the email and try again.";
export const CODE_EXPIRED_MESSAGE = "That code has expired. Select Resend Code to get a new one.";

const PRE_SIGN_UP_PREFIX = /^PreSignUp failed with error\s*/;

// The pre sign-up Lambda's messages arrive as "PreSignUp failed with error <message>", and after a
// Google redirect Cognito adds its own full stop. Returns the message ending in exactly one full stop.
export function cleanCognitoMessage(message: string) {
  const text = message.replace(PRE_SIGN_UP_PREFIX, "").trim().replace(/\.+$/, "");
  return text ? `${text}.` : GENERIC_ERROR_MESSAGE;
}

export function getErrorName(error: unknown) {
  return error instanceof Error ? error.name : undefined;
}
