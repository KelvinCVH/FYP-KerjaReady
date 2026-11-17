import { useEffect, useEffectEvent, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router";
import PastAssessments from "@/components/resume/PastAssessments";
import ResumeAssessmentView from "@/components/resume/ResumeAssessmentView";
import ResumeNotFound from "@/components/resume/ResumeNotFound";
import { useApiData } from "@/hooks/useApiData";
import { usePageTitle } from "@/hooks/usePageTitle";
import { formatDate } from "@/lib/formatDate";
import { listResumes } from "@/lib/resumeApi";

// The resume in the URL: null for the latest (/candidate/resume), false when it is not a whole number
function parseResumeId(param: string | undefined) {
  if (param === undefined) return null;
  return /^\d+$/.test(param) ? Number(param) : false;
}

// key: the shown view. It changes on each move between assessments, so every resume gets a fresh view.
// uploadedId: a resume uploaded in the current view, which is now the one shown.
type ViewSession = { param: string | undefined; key: number; uploadedId: number | null };

// Set on the URL change that follows an upload from an earlier assessment, so that view stays as it is
type KeepViewState = { keepView?: number } | null;

// /candidate/resume shows the latest assessment; /candidate/resume/<id> shows that one, with a notice when it is
// earlier than the newest. Past Assessments sits beside the main column from 2xl and below it otherwise.
export default function ResumePage() {
  usePageTitle("Resume | KerjaReady");

  const { resumeId: param } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const resumeId = parseResumeId(param);
  const { state: list, retry: retryList, refresh: refreshList } = useApiData(listResumes);

  const [session, setSession] = useState<ViewSession>({ param, key: 0, uploadedId: null });
  if (session.param !== param) {
    // A move to another assessment starts a fresh view. The URL change after an upload keeps the view, but only
    // for the view it was made from, so Back onto that history entry later still starts afresh.
    const keep = (location.state as KeepViewState)?.keepView === session.key;
    setSession({
      param,
      key: keep ? session.key : session.key + 1,
      uploadedId: keep ? session.uploadedId : null,
    });
  }

  const [announcement, setAnnouncement] = useState("");
  const headingRef = useRef<HTMLHeadingElement>(null);
  const shownKeyRef = useRef(session.key);

  const resumes = list.status === "ready" ? list.data : null;
  const newestId = resumes?.[0]?.resume_id ?? null;
  // Unknown until the list loads, and hidden if it fails: only the list says which resume is the newest
  const earlier =
    typeof resumeId === "number" && session.uploadedId === null && newestId !== null && resumeId !== newestId;
  let viewingId: number | null = null;
  if (session.uploadedId !== null) viewingId = session.uploadedId;
  else if (typeof resumeId === "number") viewingId = resumeId;
  else if (resumeId === null) viewingId = newestId;

  // After moving to another assessment: say which one is shown, and bring the page's start into view when the
  // focused control has gone (View Latest) or the heading is off screen (a row below the content)
  const onViewChange = useEffectEvent(() => {
    if (resumeId === null) setAnnouncement("Showing your latest assessment.");
    else {
      const row = resumes?.find((resume) => resume.resume_id === resumeId);
      setAnnouncement(row ? `Showing the assessment from ${formatDate(row.uploaded_at)}.` : "");
    }

    const heading = headingRef.current;
    if (!heading) return;
    const focusLost = !document.activeElement || document.activeElement === document.body;
    if (focusLost || heading.getBoundingClientRect().bottom < 0) heading.focus();
  });

  useEffect(() => {
    if (shownKeyRef.current === session.key) return;
    shownKeyRef.current = session.key;
    onViewChange();
  }, [session.key]);

  // A new upload is being tracked: list it, and point the URL at the latest without leaving the view
  function startTracking(uploadedId: number) {
    setSession((current) => ({ ...current, uploadedId }));
    refreshList();
    if (param !== undefined) {
      navigate("/candidate/resume", { replace: true, state: { keepView: session.key } satisfies KeepViewState });
    }
  }

  return (
    <div className="grid max-w-5xl grid-cols-1 gap-6 2xl:max-w-none 2xl:grid-cols-[minmax(0,64rem)_20rem] 2xl:items-start">
      <div className="min-w-0">
        <h1
          ref={headingRef}
          tabIndex={-1}
          className="rounded-md text-2xl font-semibold text-balance outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          Resume
        </h1>
        <p className="mt-2 text-base leading-relaxed text-muted-foreground">
          Upload your resume to see how it is rated on each assessed criterion.
        </p>
        <p role="status" className="sr-only">
          {announcement}
        </p>
        <div className="mt-6">
          {resumeId === false ? (
            <ResumeNotFound />
          ) : (
            <ResumeAssessmentView
              key={session.key}
              resumeId={resumeId}
              earlier={earlier}
              onTrackingStart={startTracking}
              onStatusChange={refreshList}
            />
          )}
        </div>
      </div>
      <PastAssessments state={list} viewingId={viewingId} onRetry={retryList} />
    </div>
  );
}
