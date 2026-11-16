import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { flushSync } from "react-dom";
import { Link } from "react-router";
import { cn } from "cn";
import { CircleCheck } from "lucide-react";
import FormAlert from "@/components/auth/FormAlert";
import LoadingButton from "@/components/LoadingButton";
import { profileCard } from "@/components/profile/styles";
import ResumeDropzone from "@/components/resume/ResumeDropzone";
import SelectedResumeFile from "@/components/resume/SelectedResumeFile";
import { Button } from "@/components/ui/button";
import { usePageTitle } from "@/hooks/usePageTitle";
import { getApiErrorMessage } from "@/lib/apiClient";
import { createResume, uploadResumeFile } from "@/lib/resumeApi";
import { validateResumeFile } from "@/lib/resumeFile";

// idle: no file or a file not yet uploaded. failed: the last upload failed and can be tried again.
type Phase = "idle" | "uploading" | "failed" | "uploaded";

const HELPER_ID = "resume-file-helper";

const hints: Record<Phase, string | null> = {
  idle: "The assessment starts as soon as the upload finishes.",
  uploading: "Uploading your resume. Keep this page open.",
  failed: null,
  uploaded: "The assessment can take up to a minute.",
};

export default function ResumePage() {
  usePageTitle("Resume | KerjaReady");

  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  // A file check message or a failed upload, shown in the red banner
  const [error, setError] = useState<string | null>(null);
  const [resumeId, setResumeId] = useState<number | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const chooseRef = useRef<HTMLButtonElement>(null);
  const uploadRef = useRef<HTMLButtonElement>(null);
  const viewRef = useRef<HTMLAnchorElement>(null);
  // Set while an upload runs, so a second click can't start another one
  const busyRef = useRef(false);
  const controllerRef = useRef<AbortController | null>(null);

  // Leaving the page stops an upload in progress
  useEffect(() => () => controllerRef.current?.abort(), []);

  // Closing or reloading the tab mid-upload asks the browser to confirm first
  useEffect(() => {
    if (phase !== "uploading") return;
    function warn(event: BeforeUnloadEvent) {
      event.preventDefault();
    }
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [phase]);

  function openPicker() {
    inputRef.current?.click();
  }

  // Shared by the file picker and drag and drop. The control that had focus may be gone after the
  // change, so focus moves to the one the user needs next.
  function selectFile(picked: File) {
    const message = validateResumeFile(picked);
    flushSync(() => {
      setFile(message ? null : picked);
      setError(message);
      setPhase("idle");
    });
    if (message) chooseRef.current?.focus();
    else uploadRef.current?.focus();
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    const picked = event.target.files?.[0];
    // Reset, so choosing the same file again still fires a change
    event.target.value = "";
    if (picked) selectFile(picked);
  }

  // Creates the resume record, then uploads the PDF to S3. A retry always starts again here, so it
  // gets a fresh upload form.
  async function upload() {
    if (!file || busyRef.current) return;
    const message = validateResumeFile(file);
    if (message) {
      selectFile(file);
      return;
    }

    busyRef.current = true;
    const controller = new AbortController();
    controllerRef.current = controller;
    setError(null);
    setPhase("uploading");

    try {
      const created = await createResume(file.name);
      if (controller.signal.aborted) return;
      await uploadResumeFile(created.upload, file, controller.signal);
      if (controller.signal.aborted) return;
      // Render View Assessment now, so it exists to take focus from the removed upload button
      flushSync(() => {
        setResumeId(created.resume_id);
        setPhase("uploaded");
      });
      viewRef.current?.focus();
    } catch (uploadError) {
      if (controller.signal.aborted) return;
      setError(getApiErrorMessage(uploadError));
      setPhase("failed");
    } finally {
      busyRef.current = false;
    }
  }

  const uploading = phase === "uploading";
  const uploaded = phase === "uploaded";
  const hint = hints[phase];

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-semibold text-balance">Resume</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        Upload your resume to see how it is rated on each assessed criterion.
      </p>

      <section aria-labelledby="upload-resume-heading" className={`${profileCard} mt-6`}>
        <h2 id="upload-resume-heading" className="text-xl font-semibold text-balance">
          Upload Resume
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Your resume is rated on work evidence, outcomes, skills in use and language quality.
        </p>

        {/* Picked through Choose PDF or Change File, so it stays out of the tab order */}
        <input
          ref={inputRef}
          type="file"
          name="resume"
          accept=".pdf,application/pdf"
          tabIndex={-1}
          aria-hidden="true"
          className="hidden"
          onChange={handleInputChange}
        />

        <div className="mt-5 space-y-4 border-t pt-6">
          {/* Always in the page, so screen readers announce the success message when it appears */}
          <div role="status" className="empty:hidden">
            {uploaded && (
              <p className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                <CircleCheck aria-hidden="true" className="size-4 shrink-0" />
                Resume uploaded. Your assessment has started.
              </p>
            )}
          </div>
          {error && <FormAlert message={error} />}

          {file ? (
            <SelectedResumeFile file={file} uploaded={uploaded} onChange={openPicker} changeDisabled={uploading} />
          ) : (
            <div>
              <ResumeDropzone onDrop={selectFile} onChoose={openPicker} describedBy={HELPER_ID} chooseRef={chooseRef} />
              <p id={HELPER_ID} className="mt-4 text-sm text-muted-foreground">
                PDF only, up to 5&nbsp;MB. Scanned PDFs can’t be read.
              </p>
            </div>
          )}

          {file && (
            <div className="flex items-center gap-4 pt-1">
              {uploaded && resumeId !== null ? (
                <Button asChild>
                  <Link ref={viewRef} to={`/candidate/resume/result/${resumeId}`}>
                    View Assessment
                  </Link>
                </Button>
              ) : (
                <LoadingButton
                  ref={uploadRef}
                  pending={uploading}
                  pendingLabel="Uploading…"
                  onClick={upload}
                  // Grey while uploading, so the label keeps full contrast (not a faded green)
                  className={cn(uploading && "bg-muted text-muted-foreground hover:bg-muted")}
                >
                  {phase === "failed" ? "Try Again" : "Upload and Assess"}
                </LoadingButton>
              )}
              {/* Always in the page while a file is chosen, so the uploading hint is announced */}
              <p role="status" className="text-sm text-muted-foreground">
                {hint}
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
