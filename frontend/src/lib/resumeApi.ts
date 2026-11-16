import { apiSend, ApiError } from "./apiClient";

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
