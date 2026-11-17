import { useState } from "react";
import { ChevronDown, CircleAlert, History } from "lucide-react";
import { Link } from "react-router";
import { cn } from "cn";
import StatusBadge from "@/components/StatusBadge";
import { sectionIconTile } from "@/components/profile/styles";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiDataState } from "@/hooks/useApiData";
import { formatDate } from "@/lib/formatDate";
import { RESUME_LIST_LIMIT, type ResumeSummary } from "@/lib/resumeApi";
import { ASSESSMENT_STATUS } from "@/lib/status";

type PastAssessmentsProps = {
  state: ApiDataState<ResumeSummary[]>;
  // The resume shown on the page, marked "Viewing"
  viewingId: number | null;
  onRetry: () => void;
};

const HEADING_ID = "past-assessments-heading";

function Row({ resume, viewing }: { resume: ResumeSummary; viewing: boolean }) {
  return (
    <li>
      {/* Read in DOM order (name, date, status); the grid puts the badge on the first line */}
      <Link
        to={`/candidate/resume/${resume.resume_id}`}
        aria-current={viewing ? "page" : undefined}
        className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-0.5 rounded-lg px-3 py-2.5 outline-none transition-colors duration-150 hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card aria-[current=page]:bg-muted"
      >
        {/* Cut to one line on screen; screen readers still get the whole name, and title shows it on hover */}
        <span className={cn("truncate text-sm", viewing && "font-semibold")} title={resume.file_name}>
          {resume.file_name}
        </span>
        {/* Both columns wide: the line under the badge is free, so "· Viewing" stays on one line */}
        <span className="col-span-2 col-start-1 row-start-2 text-sm text-muted-foreground tabular-nums">
          <time dateTime={resume.uploaded_at}>{formatDate(resume.uploaded_at)}</time>
          {viewing && (
            <>
              <span aria-hidden="true"> · </span>Viewing
            </>
          )}
        </span>
        <span className="col-start-2 row-start-1">
          <StatusBadge {...ASSESSMENT_STATUS[resume.status]} />
        </span>
      </Link>
    </li>
  );
}

// The candidate's uploads, newest first, each opening its assessment on this page (mockups 18 to 20).
// Beside the main column from 2xl, below it on narrower screens. Open at first; the heading collapses it.
export default function PastAssessments({ state, viewingId, onRetry }: PastAssessmentsProps) {
  // Kept while moving between assessments, because the page (and this panel) stays mounted
  const [open, setOpen] = useState(true);

  function renderBody() {
    if (state.status === "loading") {
      return (
        <div aria-busy="true">
          <p className="sr-only">Loading your past assessments…</p>
          <div aria-hidden="true" className="space-y-1">
            {[0, 1, 2].map((row) => (
              <div key={row} className="px-3 py-2.5">
                <div className="flex items-center justify-between gap-3">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-6 w-24 rounded-lg" />
                </div>
                <Skeleton className="mt-1.5 h-4 w-24" />
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (state.status === "error") {
      return (
        <div className="px-3">
          <p className="flex items-start gap-2 text-sm">
            <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-red-700" />
            We couldn’t load your past assessments. Try again.
          </p>
          <Button type="button" variant="outline" className="mt-3" onClick={onRetry}>
            Try Again
          </Button>
        </div>
      );
    }

    const resumes = state.data;
    if (resumes.length === 0) {
      return (
        <div className="flex flex-col items-center py-2 text-center">
          <div className={`${sectionIconTile} bg-muted text-foreground`}>
            <History aria-hidden="true" />
          </div>
          <p className="mt-3 text-base font-medium">No assessments yet</p>
          <p className="mt-1 text-sm text-muted-foreground">Your uploaded resumes will appear here.</p>
        </div>
      );
    }

    return (
      <>
        <ul className="space-y-1">
          {resumes.map((resume) => (
            <Row key={resume.resume_id} resume={resume} viewing={resume.resume_id === viewingId} />
          ))}
        </ul>
        {resumes.length >= RESUME_LIST_LIMIT && (
          <p className="mt-3 px-3 text-sm text-muted-foreground">Showing your {RESUME_LIST_LIMIT} most recent.</p>
        )}
      </>
    );
  }

  return (
    <Collapsible open={open} onOpenChange={setOpen} asChild>
      <nav aria-labelledby={HEADING_ID} className="rounded-xl border bg-card p-5">
        {/* Disclosure pattern: the button sits inside the heading, so it keeps the heading's place in the outline */}
        <h2 id={HEADING_ID} className="text-xl font-semibold text-balance">
          <CollapsibleTrigger className="group -my-1.5 flex min-h-11 w-full items-center justify-between gap-3 rounded-md text-left outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card">
            Past Assessments
            <ChevronDown
              aria-hidden="true"
              className="size-5 shrink-0 text-muted-foreground transition-transform duration-150 group-data-[state=open]:rotate-180"
            />
          </CollapsibleTrigger>
        </h2>
        <CollapsibleContent>
          <p className="mt-1 text-sm text-muted-foreground">Your uploads, newest first.</p>
          <div className="mt-4 border-t pt-3">{renderBody()}</div>
        </CollapsibleContent>
      </nav>
    </Collapsible>
  );
}
