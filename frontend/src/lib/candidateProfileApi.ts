import { apiGet, apiSend } from "./apiClient";

// A target role from the knowledge base
export type Role = { role_id: number; title: string };

export type CandidateProfile = {
  email: string;
  full_name: string;
  account_type: "candidate";
  target_role: Role | null;
};

// The signed-in candidate's account details and saved target role
export function getCandidateProfile() {
  return apiGet<CandidateProfile>("/candidate/profile");
}

// Every role in the knowledge base, sorted by title
export async function getRoles() {
  const { roles } = await apiGet<{ roles: Role[] }>("/roles");
  return roles;
}

// Saves the candidate's target role, or clears it when roleId is null. Returns the role as saved.
export async function saveTargetRole(roleId: number | null) {
  const { target_role } = await apiSend<{ target_role: Role | null }>("PUT", "/candidate/target-role", {
    role_id: roleId,
  });
  return target_role;
}
