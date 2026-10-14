// Keeps the email awaiting a password reset code across a page refresh on /reset-password
const STORAGE_KEY = "kerjaready.pendingPasswordReset";

export function savePendingPasswordReset(email: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY, email);
  } catch {
    // Storage can be unavailable (private mode, blocked site data). Router state still carries the email.
  }
}

export function readPendingPasswordReset(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY) || null;
  } catch {
    return null;
  }
}

export function clearPendingPasswordReset() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to clear when storage is unavailable
  }
}
