import type { ReactNode } from "react";
import { CircleAlert, CircleCheck, Clock, FileText } from "lucide-react";
import FormAlert from "@/components/auth/FormAlert";
import LoadingButton from "@/components/LoadingButton";
import { profileCard, sectionIconTile } from "@/components/profile/styles";
import { Button } from "@/components/ui/button";
import { useAssessmentStatus } from "@/hooks/useAssessmentStatus";
import type { AssessmentState, AssessmentStatus, FailureReason } from "@/lib/resumeApi";
import AssessmentSteps from "./AssessmentSteps";

// After done: "loading" while the ratings are fetched, "failed" when that failed (Open Results Now shows), and
// "reloading" while Open Results Now fetches them again
export type ResultsLoad = "idle" | "loading" | "failed" | "reloading";

type AssessmentProgressCardProps = {
  resumeId: number;
  fileName: string;
  initial: AssessmentState;
  // Runs once when the assessment is done, to load and show the ratings
  onDone: () => void;
  // Runs each time the status moves on, so the page can refresh the Past Assessments list
  onStatusChange?: (status: AssessmentStatus) => void;
  resultsLoad: ResultsLoad;
  onOpenResults: () => void;
  onUploadDifferent: () => void;
};

// What a failed run tells the candidate. Only "error" offers Try Again: the same file fails the same way otherwise.
function failureText(reason: FailureReason | null, fileName: string) {
  if (reason === "not_pdf") {
    return `We couldn’t open ${fileName} as a PDF. Export your resume as a PDF from Word or Google Docs and upload it again.`;
  }
  if (reason === "no_text") {
    return `We couldn’t find readable text in ${fileName}. It may be a scanned image or password-protected. Export it as a PDF from Word or Google Docs and upload it again.`;
  }
  return `Something went wrong while assessing ${fileName}. Try again.`;
}

// Short text for screen readers when the stage changes. The card itself is not a live region.
const ANNOUNCEMENTS: Partial<Record<AssessmentStatus, string>> = {
  uploaded: "Assessment starting.",
  reading: "Reading your resume.",
  rating: "Rating your resume.",
  done: "Assessment complete.",
};

type OutcomeProps = {
  tile: string;
  icon: ReactNode;
  heading: string;
  text: string;
  children: ReactNode;
};

// The icon tile layout for a finished run: failed, timed out, or complete when the ratings didn't load
function Outcome({ tile, icon, heading, text, children }: OutcomeProps) {
  return (
    <div className="flex items-start gap-4">
      <div className={`${sectionIconTile} ${tile}`}>{icon}</div>
      <div className="min-w-0 flex-1">
        <h2 className="text-xl font-semibold text-balance">{heading}</h2>
        <p className="mt-1 text-sm leading-relaxed break-words text-muted-foreground">{text}</p>
        <div className="mt-4 space-y-4">{children}</div>
      </div>
    </div>
  );
}

// Progress of one resume's assessment, under the upload card (mockups 11 to 17)
export default function AssessmentProgressCard({
  resumeId,
  fileName,
  initial,
  onDone,
  onStatusChange,
  resultsLoad,
  onOpenResults,
  onUploadDifferent,
}: AssessmentProgressCardProps) {
  const { status, failureReason, loadError, retry, retrying, retryError } = useAssessmentStatus(
    resumeId,
    initial,
    onDone,
    onStatusChange,
  );

  const uploadDifferent = (primary: boolean) => (
    <Button type="button" variant={primary ? "default" : "outline"} onClick={onUploadDifferent}>
      Upload a Different File
    </Button>
  );

  function renderContent() {
    if (loadError) {
      return (
        <Outcome
          tile="bg-red-50 text-red-700"
          icon={<CircleAlert aria-hidden="true" />}
          heading="Progress Unavailable"
          text={loadError}
        >
          {uploadDifferent(true)}
        </Outcome>
      );
    }

    if (status === "failed" || status === "timed_out") {
      const timedOut = status === "timed_out";
      const canRetry = timedOut || (failureReason !== "not_pdf" && failureReason !== "no_text");
      return (
        <Outcome
          tile={timedOut ? "bg-amber-50 text-amber-800" : "bg-red-50 text-red-700"}
          icon={timedOut ? <Clock aria-hidden="true" /> : <CircleAlert aria-hidden="true" />}
          heading={timedOut ? "Taking Longer Than Expected" : "Assessment Failed"}
          text={
            timedOut
              ? `The assessment of ${fileName} hasn’t finished after 2 minutes. Try again.`
              : failureText(failureReason, fileName)
          }
        >
          {retryError && <FormAlert message={retryError} />}
          <div className="flex flex-wrap gap-3">
            {canRetry && (
              <LoadingButton pending={retrying} pendingLabel="Starting…" onClick={retry}>
                Try Again
              </LoadingButton>
            )}
            {uploadDifferent(!canRetry)}
          </div>
        </Outcome>
      );
    }

    if (status === "done" && (resultsLoad === "failed" || resultsLoad === "reloading")) {
      return (
        <Outcome
          tile="bg-emerald-50 text-emerald-800"
          icon={<CircleCheck aria-hidden="true" />}
          heading="Assessment Complete"
          text="Your ratings are ready."
        >
          <div>
            <LoadingButton pending={resultsLoad === "reloading"} pendingLabel="Opening…" onClick={onOpenResults}>
              Open Results Now
            </LoadingButton>
          </div>
        </Outcome>
      );
    }

    return (
      <>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="text-xl font-semibold text-balance">Assessing Your Resume</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              This usually takes 1 to 2 minutes. You can leave this page and come back.
            </p>
          </div>
          <p className="flex max-w-60 min-w-0 shrink-0 items-center gap-2 rounded-lg border px-3 py-1.5 text-sm">
            <FileText aria-hidden="true" className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate" title={fileName}>
              {fileName}
            </span>
          </p>
        </div>
        <AssessmentSteps status={status} />
      </>
    );
  }

  // Read out on each change. A failure is read from its heading and text; the card itself is not a live region.
  const finished = status === "failed" || status === "timed_out";
  let announcement = ANNOUNCEMENTS[status] ?? null;
  if (loadError) announcement = loadError;
  else if (status === "timed_out") announcement = "The assessment is taking longer than expected.";
  else if (status === "failed") announcement = `Assessment failed. ${failureText(failureReason, fileName)}`;
  else if (status === "done" && resultsLoad === "failed") announcement = "Assessment complete. Your ratings are ready.";

  return (
    <section
      aria-label={finished ? "Assessment result" : "Assessment progress"}
      aria-busy={resultsLoad === "loading" || undefined}
      className={profileCard}
    >
      <p role="status" className="sr-only">
        {announcement}
      </p>
      {renderContent()}
    </section>
  );
}
