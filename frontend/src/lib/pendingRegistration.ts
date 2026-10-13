import type { AccountType } from "./registrationValidation";

// Keeps the email awaiting verification across a page refresh on /register/verify
export type PendingRegistration = {
  email: string;
  accountType?: AccountType;
};

const STORAGE_KEY = "kerjaready.pendingRegistration";

export function savePendingRegistration(pending: PendingRegistration) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(pending));
  } catch {
    // Storage can be unavailable (private mode, blocked site data). Router state still carries the email.
  }
}

export function readPendingRegistration(): PendingRegistration | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;

    const { email, accountType } = parsed as Record<string, unknown>;
    if (typeof email !== "string" || !email) return null;
    return {
      email,
      accountType:
        accountType === "candidate" || accountType === "recruiter" ? accountType : undefined,
    };
  } catch {
    return null;
  }
}

export function clearPendingRegistration() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to clear when storage is unavailable
  }
}
