// Client-side checks for the Create Account flow. Each returns an error message, or null when valid.

export type AccountType = "candidate" | "recruiter";

export const PASSWORD_HINT =
  "Use at least 8 characters, including uppercase and lowercase letters, a number and a symbol.";

// Cognito's accepted special characters, so the browser and the user pool agree
const SYMBOL_PATTERN = /[\^$*.[\]{}()?"!@#%&/\\,><':;|_~`=+-]/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function normaliseEmail(email: string) {
  return email.trim().toLowerCase();
}

export function validateFullName(fullName: string) {
  return fullName.trim() ? null : "Enter your full name.";
}

export function validateCompanyName(companyName: string) {
  return companyName.trim() ? null : "Enter your company name.";
}

export function validateEmail(email: string) {
  const normalised = normaliseEmail(email);
  if (!normalised) return "Enter your email address.";
  if (!EMAIL_PATTERN.test(normalised)) {
    return "This email address is not valid. Check it and try again.";
  }
  return null;
}

// Returns the first password rule that is not met, in the order the hint lists them
export function getPasswordRuleError(password: string) {
  if (password.length < 8) return "Use at least 8 characters.";
  if (!/[A-Z]/.test(password)) return "Add at least one uppercase letter.";
  if (!/[a-z]/.test(password)) return "Add at least one lowercase letter.";
  if (!/[0-9]/.test(password)) return "Add at least one number.";
  if (!SYMBOL_PATTERN.test(password)) return "Add at least one symbol, such as ! or #.";
  return null;
}

export function validatePassword(password: string) {
  if (!password) return "Enter a password.";
  return getPasswordRuleError(password);
}

export function validateCode(code: string) {
  const trimmed = code.trim();
  if (!trimmed) return "Enter the 6-digit code from your email.";
  if (!/^\d{6}$/.test(trimmed)) return "The code is 6 digits. Check the email and try again.";
  return null;
}
