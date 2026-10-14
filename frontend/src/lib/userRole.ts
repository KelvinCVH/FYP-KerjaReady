import { fetchAuthSession, signOut } from "aws-amplify/auth";
import type { NavigateFunction } from "react-router";
import { saveSignInError } from "./signInNotice";

export type UserRole = "recruiter" | "candidate";

// Matches the dashboard routes in router.tsx
export const DASHBOARD_PATHS: Record<UserRole, string> = {
  candidate: "/candidate/dashboard",
  recruiter: "/recruiter/dashboard",
};

export const NO_ROLE_MESSAGE = "We couldn’t load your account. Try again.";

// Returns null when signed out, otherwise the role from the ID token's cognito:groups (null if none).
// Google users also carry an automatic "<pool>_Google" group, so search the list instead of taking the first.
async function readRole(forceRefresh: boolean): Promise<UserRole | null | undefined> {
  try {
    const { tokens } = await fetchAuthSession({ forceRefresh });
    if (!tokens) return undefined;
    const groups = tokens.idToken?.payload["cognito:groups"];
    const list = Array.isArray(groups) ? groups : [];
    if (list.includes("recruiter")) return "recruiter";
    if (list.includes("candidate")) return "candidate";
    return null;
  } catch {
    return undefined;
  }
}

// The signed-in user's role, or null when signed out or when no role group is found
export async function getUserRole(): Promise<UserRole | null> {
  const role = await readRole(false);
  if (role !== null) return role ?? null;
  // A new Google account can get its group after the first token was issued
  return (await readRole(true)) ?? null;
}

export async function hasSession() {
  try {
    const { tokens } = await fetchAuthSession();
    return Boolean(tokens);
  } catch {
    return false;
  }
}

// Saves the no-role error for Sign In, then signs the user out. Google users pass through Cognito's /logout.
export async function signOutWithoutRole() {
  saveSignInError(NO_ROLE_MESSAGE);
  try {
    await signOut();
  } catch {
    // Sign In still shows the saved error
  }
}

// Sends a signed-in user to their dashboard and returns true. Without a role, it signs the user out
// with the no-role error and returns false.
export async function redirectSignedInUser(navigate: NavigateFunction) {
  const role = await getUserRole();
  if (role) {
    navigate(DASHBOARD_PATHS[role], { replace: true });
    return true;
  }
  await signOutWithoutRole();
  return false;
}
