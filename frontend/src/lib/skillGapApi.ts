import { apiGet } from "./apiClient";

// How the assessment found a skill: its name in the resume (lexical), a related tool that implies it (implied),
// or a resume line close in meaning (semantic)
export type MatchMethod = "lexical" | "implied" | "semantic";

// The candidate's saved target role, with the entry-level Malaysian JobStreet postings its skill profile comes from
export type SkillGapRole = {
  role_id: number;
  title: string;
  posting_count: number;
  // The earliest and latest posting dates, "YYYY-MM-DD"; null when the role has no postings
  first_posted: string | null;
  last_posted: string | null;
};

// One skill in the role profile and how often the role's postings ask for it
export type SkillDemand = {
  skill_id: number;
  name: string;
  // Share of the role's postings that ask for the skill, from 0 to 1
  demand_share: number;
  // How many of the role's postings ask for it, counted by the API
  postings: number;
};

// A skill the assessment found in the resume, with the resume line that shows it.
// The line is resume content: show it on the page, never log it.
export type EvidencedSkill = SkillDemand & { evidence: string; match_method: MatchMethod };

export type SkillGap = {
  resume_id: number;
  // null when the candidate hasn't chosen a target role; both lists are then empty
  target_role: SkillGapRole | null;
  // Both ordered by demand share, highest first, then by name
  evidenced: EvidencedSkill[];
  not_evidenced: SkillDemand[];
};

// The skills of the candidate's saved target role, split by whether this resume evidences them.
// 404 when the resume is missing, still uploading or not theirs; 409 when its assessment hasn't finished.
export function getSkillGap(resumeId: number) {
  return apiGet<SkillGap>(`/candidate/resumes/${resumeId}/skill-gap`);
}
