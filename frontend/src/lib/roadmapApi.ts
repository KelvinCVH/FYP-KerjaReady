import { apiGet, apiSend } from "./apiClient";

// The latest assessed resume the roadmap is written from
export type RoadmapResume = {
  resume_id: number;
  file_name: string;
  // ISO 8601 in UTC
  assessed_at: string;
};

// The candidate's saved target role, with the number of entry-level Malaysian job postings behind it
export type RoadmapRole = { role_id: number; title: string; posting_count: number };

export type RoadmapRunStatus = "running" | "done" | "failed";

// One run of the background agent that writes the roadmap
export type RoadmapRun = {
  run_id: number;
  status: RoadmapRunStatus;
  // ISO 8601 in UTC
  created_at: string;
  finished_at: string | null;
};

// How to move one low-rated assessment criterion up a level
export type ResumeStep = {
  criterion: string;
  level: number;
  level_label: string;
  next_label: string;
  how_to_improve: string;
  // May hold [placeholders] for the candidate to fill in
  example_line: string;
  linked_skills: string[];
};

export type PracticeProject = { title: string; description: string; deliverable: string };

// One skill not evidenced in the resume, in demand order, with how to learn it and show it.
// Every text field is written by AI: show it as plain text only, and never log it.
export type SkillMilestone = {
  skill: string;
  postings: number;
  role_postings: number;
  why_it_matters: string | null;
  prerequisites: string | null;
  // The full sentence on what to learn first, for the details panel
  learning_order: string | null;
  // The name of another milestone skill to learn first, for the card
  learn_after: string | null;
  objectives: string[];
  key_topics: string[];
  practice_project: PracticeProject | null;
  ready_when: string[];
  // May hold [placeholders] for the candidate to fill in
  resume_line: string;
  search_terms: string[];
  source_posting_ids: number[];
};

export type Roadmap = {
  // 0 to 2 items
  resume_steps: ResumeStep[];
  // 0 to 6 items, in demand order
  skill_milestones: SkillMilestone[];
};

export type RoadmapResponse = {
  // null when the candidate has no assessed resume
  resume: RoadmapResume | null;
  // null when the candidate has no target role
  target_role: RoadmapRole | null;
  // The latest run for this resume and role; null when there has never been one
  run: RoadmapRun | null;
  // Present only when run.status is "done"
  roadmap?: Roadmap | null;
};

// The candidate's latest roadmap run and, once it is done, the roadmap itself
export function getRoadmap() {
  return apiGet<RoadmapResponse>("/candidate/roadmap");
}

// Starts writing a roadmap for the latest assessed resume and the current target role. If a run is already running,
// the API returns that one. 409 when there is no assessed resume or no target role.
export async function startRoadmap() {
  const { run } = await apiSend<{ run: RoadmapRun }>("POST", "/candidate/roadmap");
  return run;
}
