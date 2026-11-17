import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Info } from "lucide-react";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import AssessmentProgressCard, { type ResultsLoad } from "@/components/resume/AssessmentProgressCard";
import CurrentResumeBar from "@/components/resume/CurrentResumeBar";
import ResumePreview from "@/components/resume/ResumePreview";
import ResumeRatings from "@/components/resume/ResumeRatings";
import ResumeSkeleton from "@/components/resume/ResumeSkeleton";
import ResumeUploadCard from "@/components/resume/ResumeUploadCard";
import { useApiData } from "@/hooks/useApiData";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  getLatestResume,
  type AssessmentState,
  type LatestResume,
  type ResumeRatings as Ratings,
} from "@/lib/resumeApi";
import { RUBRIC } from "@/lib/rubric";

// A "done" resume whose ratings can't be shown
const NO_RATINGS_LINE = "We couldn’t assess your last resume. Upload it again or try another PDF.";

// The resume whose progress card is shown
type Tracked = { resumeId: number; fileName: string; initial: AssessmentState };

// Every criterion has a whole-number level from 0 to 3
function hasValidRatings(ratings: Ratings | null): ratings is Ratings {
  return (
    ratings !== null &&
    RUBRIC.every(({ key }) => Number.isInteger(ratings[key]) && ratings[key] >= 0 && ratings[key] <= 3)
  );
}

function hasResults(resume: LatestResume | null | undefined): resume is LatestResume & { ratings: Ratings } {
  return resume?.status === "done" && hasValidRatings(resume.ratings);
}

export default function ResumePage() {
  usePageTitle("Resume | KerjaReady");

  const { state: page, retry, setData } = useApiData(getLatestResume);
  // Upload New Resume swaps the ratings for the upload card until Cancel
  const [replacing, setReplacing] = useState(false);
  // The resume uploaded on this page. Takes over from the one the page loaded with.
  const [uploaded, setUploaded] = useState<Tracked | null>(null);
  // The loaded resume after Upload a Different File, so its progress card stays hidden
  const [dismissedId, setDismissedId] = useState<number | null>(null);
  // Set by the first upload on this page: from then on, the old ratings are no longer the latest
  const [hasUploaded, setHasUploaded] = useState(false);
  // Bumped to reset the upload card to its empty state
  const [uploadCardKey, setUploadCardKey] = useState(0);
  const [resultsLoad, setResultsLoad] = useState<ResultsLoad>("idle");
  const [announcement, setAnnouncement] = useState("");

  const uploadHeadingRef = useRef<HTMLHeadingElement>(null);
  const uploadNewRef = useRef<HTMLButtonElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);

  const latest = page.status === "ready" ? page.data : null;
  const loadedTracking: Tracked | null =
    latest && latest.status !== "done" && latest.resume_id !== dismissedId
      ? {
          resumeId: latest.resume_id,
          fileName: latest.file_name,
          initial: { status: latest.status, failure_reason: latest.failure_reason },
        }
      : null;
  const tracked = uploaded ?? loadedTracking;

  // Render the new view first, so the element that takes focus exists
  function startReplacing() {
    flushSync(() => setReplacing(true));
    uploadHeadingRef.current?.focus();
  }

  function cancelReplacing() {
    flushSync(() => setReplacing(false));
    uploadNewRef.current?.focus();
  }

  function startTracking(resumeId: number, fileName: string) {
    setUploaded({ resumeId, fileName, initial: { status: "uploaded", failure_reason: null } });
    setHasUploaded(true);
    setResultsLoad("idle");
    setAnnouncement("");
  }

  // The assessment finished: load its ratings and swap both cards for them, without a reload
  async function showResults(retrying = false) {
    setResultsLoad(retrying ? "reloading" : "loading");
    try {
      const resume = await getLatestResume();
      if (!hasResults(resume)) throw new Error("No ratings to show");
      // Focus was on a card that is about to go, so it moves to the ratings view's first control
      const hadFocus = cardsRef.current?.contains(document.activeElement) ?? false;
      flushSync(() => {
        setData(() => resume);
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
      return <ProfileLoadError status={page.httpStatus} message={page.message} onRetry={retry} />;
    }

    if (hasResults(latest) && !replacing && !uploaded) {
      return (
        <div className="space-y-6">
          <CurrentResumeBar
            fileName={latest.file_name}
            uploadedAt={latest.uploaded_at}
            onUploadNew={startReplacing}
            uploadNewRef={uploadNewRef}
          />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ResumeRatings ratings={latest.ratings} />
            <ResumePreview url={latest.view_url} />
          </div>
        </div>
      );
    }

    const showNoRatingsLine = latest?.status === "done" && !hasResults(latest) && !uploaded;
    // Cancel returns to the old ratings, so it goes once an upload makes them out of date
    const canCancel = replacing && !hasUploaded;
    return (
      <div ref={cardsRef} className="space-y-6">
        {showNoRatingsLine && (
          <p className="flex items-start gap-2 text-sm text-muted-foreground">
            <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            {NO_RATINGS_LINE}
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
            onDone={() => void showResults()}
            resultsLoad={resultsLoad}
            onOpenResults={() => void showResults(true)}
            onUploadDifferent={uploadDifferent}
          />
        )}
      </div>
    );
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-semibold text-balance">Resume</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        Upload your resume to see how it is rated on each assessed criterion.
      </p>
      <p role="status" className="sr-only">
        {announcement}
      </p>
      <div className="mt-6">{renderContent()}</div>
    </div>
  );
}
