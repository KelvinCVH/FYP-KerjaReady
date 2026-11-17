import { apiGet, apiSend, ApiError } from "./apiClient";
import type { CriterionKey } from "./rubric";

// One language error the checker found: the words from the resume and why they were flagged
export type LanguageError = { text: string; rule: string; message: string };

// Levels are 0 to 3, keyed by rubric criterion. Show rubric names, never these keys.
export type ResumeRatings = Record<CriterionKey, number> & {
  a1_work_link: string | null;
  b2_errors: LanguageError[];
  model_version: string;
  rated_at: string;
};

export type LatestResume = {
  resume_id: number;
  file_name: string;
  status: "assessing" | "done" | "failed";
  failure_reason: "not_pdf" | "no_text" | "error" | null;
  // ISO 8601 in UTC
  uploaded_at: string;
  // Presigned link to the PDF, valid for an hour
  view_url: string;
  // null until the status is "done"
  ratings: ResumeRatings | null;
};

// The signed-in candidate's latest resume, or null when they have not uploaded one
export async function getLatestResume() {
  const { resume } = await apiGet<{ resume: LatestResume | null }>("/candidate/resumes/latest");
  return resume;
}

// A one-time S3 upload form: POST to url with every field, then the file
export type ResumeUploadTarget = { url: string; fields: Record<string, string> };

export type CreatedResume = { resume_id: number; upload: ResumeUploadTarget };

const UPLOAD_FAILED_MESSAGE = "We couldn’t upload your resume. Check your connection and try again.";

// Creates the resume record and returns the S3 form to upload the PDF with
export function createResume(fileName: string) {
  return apiSend<CreatedResume>("POST", "/candidate/resumes", { file_name: fileName });
}

// Uploads the PDF straight to S3. Plain fetch, so the API's access token is never sent to S3.
export async function uploadResumeFile(upload: ResumeUploadTarget, file: File, signal?: AbortSignal) {
  const form = new FormData();
  for (const [key, value] of Object.entries(upload.fields)) form.append(key, value);
  // Last: S3 ignores any field after the file
  form.append("file", file);

  let response: Response;
  try {
    // No headers: the browser sets the multipart boundary
    response = await fetch(upload.url, { method: "POST", body: form, signal });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(0, UPLOAD_FAILED_MESSAGE);
  }
  // S3 answers 204 on success
  if (!response.ok) throw new ApiError(response.status, UPLOAD_FAILED_MESSAGE);
}
