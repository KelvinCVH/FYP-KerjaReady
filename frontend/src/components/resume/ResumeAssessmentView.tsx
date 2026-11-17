import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Info } from "lucide-react";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import { useApiData } from "@/hooks/useApiData";
import {
  getLatestResume,
  getResume,
  type AssessmentState,
  type ResumeAssessment,
  type ResumeRatings as Ratings,
} from "@/lib/resumeApi";
import { RUBRIC } from "@/lib/rubric";
import AssessmentProgressCard, { type ResultsLoad } from "./AssessmentProgressCard";
import CurrentResumeBar from "./CurrentResumeBar";
import EarlierAssessmentNotice from "./EarlierAssessmentNotice";
import ResumeNotFound from "./ResumeNotFound";
import ResumePreview from "./ResumePreview";
import ResumeRatings from "./ResumeRatings";
import ResumeSkeleton from "./ResumeSkeleton";
import ResumeUploadCard from "./ResumeUploadCard";

// A "done" resume whose ratings can't be shown
const NO_RATINGS_LATEST = "We couldn’t assess your last resume. Upload it again or try another PDF.";
const NO_RATINGS_EARLIER = "We couldn’t assess this resume. Upload it again or try another PDF.";

// The resume whose progress card is shown
type Tracked = { resumeId: number; fileName: string; initial: AssessmentState };

// Every criterion has a whole-number level from 0 to 3
function hasValidRatings(ratings: Ratings | null): ratings is Ratings {
  return (
    ratings !== null &&
    RUBRIC.every(({ key }) => Number.isInteger(ratings[key]) && ratings[key] >= 0 && ratings[key] <= 3)
  );
}

function hasResults(
  resume: ResumeAssessment | null | undefined,
): resume is ResumeAssessment & { ratings: Ratings } {
  return resume?.status === "done" && hasValidRatings(resume.ratings);
}

type ResumeAssessmentViewProps = {
  // null: the latest resume (/candidate/resume). A number: that resume (/candidate/resume/<id>).
  // Read once: the page gives each resume its own view (key).
  resumeId: number | null;
  // The resume is older than the newest one in Past Assessments, so the notice shows above it
  earlier: boolean;
  // A new upload reached S3 and its progress is now shown
  onTrackingStart: (resumeId: number) => void;
  // The shown assessment moved on a stage, finished or started again
  onStatusChange: () => void;
};

// One resume's assessment: its ratings and PDF once done, otherwise the upload card with its progress below.
// Upload New Resume and the progress card work the same for the latest resume and an earlier one.
export default function ResumeAssessmentView({
  resumeId,
  earlier,
  onTrackingStart,
  onStatusChange,
}: ResumeAssessmentViewProps) {
  const [load] = useState<() => Promise<ResumeAssessment | null>>(() =>
    resumeId === null ? getLatestResume : () => getResume(resumeId),
  );
  const { state: page, retry, setData } = useApiData(load);
  // Upload New Resume swaps the ratings for the upload card until Cancel
  const [replacing, setReplacing] = useState(false);
  // The resume uploaded in this view. Takes over from the one the view loaded with.
  const [uploaded, setUploaded] = useState<Tracked | null>(null);
  // The loaded resume after Upload a Different File, so its progress card stays hidden
  const [dismissedId, setDismissedId] = useState<number | null>(null);
  // Set by the first upload in this view: from then on, the old ratings are no longer the latest
  const [hasUploaded, setHasUploaded] = useState(false);
  // Bumped to reset the upload card to its empty state
  const [uploadCardKey, setUploadCardKey] = useState(0);
  const [resultsLoad, setResultsLoad] = useState<ResultsLoad>("idle");
  const [announcement, setAnnouncement] = useState("");

  const uploadHeadingRef = useRef<HTMLHeadingElement>(null);
  const uploadNewRef = useRef<HTMLButtonElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);

  const resume = page.status === "ready" ? page.data : null;
  const loadedTracking: Tracked | null =
    resume && resume.status !== "done" && resume.resume_id !== dismissedId
      ? {
          resumeId: resume.resume_id,
          fileName: resume.file_name,
          initial: { status: resume.status, failure_reason: resume.failure_reason },
        }
      : null;
  const tracked = uploaded ?? loadedTracking;
  const notice = earlier && resume && !uploaded ? <EarlierAssessmentNotice uploadedAt={resume.uploaded_at} /> : null;

  // Render the new view first, so the element that takes focus exists
  function startReplacing() {
    flushSync(() => setReplacing(true));
    uploadHeadingRef.current?.focus();
  }

  function cancelReplacing() {
    flushSync(() => setReplacing(false));
    uploadNewRef.current?.focus();
  }

  function startTracking(newId: number, fileName: string) {
    setUploaded({ resumeId: newId, fileName, initial: { status: "uploaded", failure_reason: null } });
    setHasUploaded(true);
    setResultsLoad("idle");
    setAnnouncement("");
    onTrackingStart(newId);
  }

  // The assessment finished: load its ratings and swap both cards for them, without a reload
  async function showResults(doneId: number, retrying = false) {
    setResultsLoad(retrying ? "reloading" : "loading");
    try {
      const done = await getResume(doneId);
      if (!hasResults(done)) throw new Error("No ratings to show");
      // Focus was on a card that is about to go, so it moves to the ratings view's first control
      const hadFocus = cardsRef.current?.contains(document.activeElement) ?? false;
      flushSync(() => {
        setData(() => done);
        setUploaded(null);
        setReplacing(false);
        setResultsLoad("idle");
        setAnnouncement("Your ratings are ready.");
      });
      if (hadFocus) uploadNewRef.current?.focus();
    } catch {
      setResultsLoad("failed");
    }
  }

  function uploadDifferent() {
    flushSync(() => {
      if (tracked) setDismissedId(tracked.resumeId);
      setUploaded(null);
      setResultsLoad("idle");
      setUploadCardKey((key) => key + 1);
    });
    uploadHeadingRef.current?.focus();
  }

  function renderContent() {
    if (page.status === "loading") return <ResumeSkeleton />;
    if (page.status === "error") {
      if (resumeId !== null && page.httpStatus === 404) return <ResumeNotFound message={page.message} />;
      return <ProfileLoadError status={page.httpStatus} message={page.message} onRetry={retry} />;
    }

    if (hasResults(resume) && !replacing && !uploaded) {
      return (
        <div className="space-y-6">
          {notice}
          <CurrentResumeBar
            fileName={resume.file_name}
            uploadedAt={resume.uploaded_at}
            onUploadNew={startReplacing}
            uploadNewRef={uploadNewRef}
          />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ResumeRatings ratings={resume.ratings} />
            <ResumePreview url={resume.view_url} />
          </div>
        </div>
      );
    }

    const showNoRatingsLine = resume?.status === "done" && !hasResults(resume) && !uploaded;
    // Cancel returns to the old ratings, so it goes once an upload makes them out of date
    const canCancel = replacing && !hasUploaded;
    return (
      <div ref={cardsRef} className="space-y-6">
        {notice}
        {showNoRatingsLine && (
          <p className="flex items-start gap-2 text-sm text-muted-foreground">
            <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            {resumeId === null ? NO_RATINGS_LATEST : NO_RATINGS_EARLIER}
          </p>
        )}
        <ResumeUploadCard
          key={uploadCardKey}
          onCancel={canCancel ? cancelReplacing : undefined}
          headingRef={uploadHeadingRef}
          onUploaded={startTracking}
          existingFileName={uploaded ? undefined : loadedTracking?.fileName}
        />
        {tracked && (
          <AssessmentProgressCard
            key={tracked.resumeId}
            resumeId={tracked.resumeId}
            fileName={tracked.fileName}
            initial={tracked.initial}
            onDone={() => void showResults(tracked.resumeId)}
            onStatusChange={onStatusChange}
            resultsLoad={resultsLoad}
            onOpenResults={() => void showResults(tracked.resumeId, true)}
            onUploadDifferent={uploadDifferent}
          />
        )}
      </div>
    );
  }

  return (
    <>
      <p role="status" className="sr-only">
        {announcement}
      </p>
      {renderContent()}
    </>
  );
}
