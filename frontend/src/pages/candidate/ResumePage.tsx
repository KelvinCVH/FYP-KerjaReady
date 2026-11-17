import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Info } from "lucide-react";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import CurrentResumeBar from "@/components/resume/CurrentResumeBar";
import ResumePreview from "@/components/resume/ResumePreview";
import ResumeRatings from "@/components/resume/ResumeRatings";
import ResumeSkeleton from "@/components/resume/ResumeSkeleton";
import ResumeUploadCard from "@/components/resume/ResumeUploadCard";
import { useApiData } from "@/hooks/useApiData";
import { usePageTitle } from "@/hooks/usePageTitle";
import { getLatestResume, type LatestResume, type ResumeRatings as Ratings } from "@/lib/resumeApi";
import { RUBRIC } from "@/lib/rubric";

// Shown above the upload card when the latest resume has no ratings to show. KR-93 replaces these lines.
const STATUS_LINES = {
  assessing: "Your last resume is still being assessed. Reopen this page in a couple of minutes.",
  failed: "We couldn’t assess your last resume. Upload it again or try another PDF.",
};

// Every criterion has a whole-number level from 0 to 3
function hasValidRatings(ratings: Ratings | null): ratings is Ratings {
  return (
    ratings !== null &&
    RUBRIC.every(({ key }) => Number.isInteger(ratings[key]) && ratings[key] >= 0 && ratings[key] <= 3)
  );
}

// "done" without usable ratings is treated as a failed assessment
function statusLineFor(resume: LatestResume | null) {
  if (!resume) return null;
  return resume.status === "assessing" ? STATUS_LINES.assessing : STATUS_LINES.failed;
}

export default function ResumePage() {
  usePageTitle("Resume | KerjaReady");

  const { state: page, retry } = useApiData(getLatestResume);
  // Upload New Resume swaps the ratings for the upload card until Cancel
  const [replacing, setReplacing] = useState(false);
  const uploadHeadingRef = useRef<HTMLHeadingElement>(null);
  const uploadNewRef = useRef<HTMLButtonElement>(null);

  // Render the new view first, so the element that takes focus exists
  function startReplacing() {
    flushSync(() => setReplacing(true));
    uploadHeadingRef.current?.focus();
  }

  function cancelReplacing() {
    flushSync(() => setReplacing(false));
    uploadNewRef.current?.focus();
  }

  function renderContent() {
    if (page.status === "loading") return <ResumeSkeleton />;
    if (page.status === "error") {
      return <ProfileLoadError status={page.httpStatus} message={page.message} onRetry={retry} />;
    }

    const resume = page.data;
    if (resume?.status === "done" && hasValidRatings(resume.ratings)) {
      if (replacing) return <ResumeUploadCard onCancel={cancelReplacing} headingRef={uploadHeadingRef} />;
      return (
        <div className="space-y-6">
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

    const statusLine = statusLineFor(resume);
    return (
      <div className="space-y-4">
        {statusLine && (
          <p className="flex items-start gap-2 text-sm text-muted-foreground">
            <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            {statusLine}
          </p>
        )}
        <ResumeUploadCard />
      </div>
    );
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-semibold text-balance">Resume</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        Upload your resume to see how it is rated on each assessed criterion.
      </p>
      <div className="mt-6">{renderContent()}</div>
    </div>
  );
}
