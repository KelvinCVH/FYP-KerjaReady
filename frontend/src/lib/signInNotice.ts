// Carries an error to /sign-in across a full page load, such as Cognito's /logout redirect after a
// Google sign-in, where router state does not survive
const STORAGE_KEY = "kerjaready.signInError";

export function saveSignInError(message: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY, message);
  } catch {
    // Storage can be unavailable (private mode, blocked site data). Sign In then shows no message.
  }
}

export function readSignInError(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY) || null;
  } catch {
    return null;
  }
}

export function clearSignInError() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to clear when storage is unavailable
  }
}
