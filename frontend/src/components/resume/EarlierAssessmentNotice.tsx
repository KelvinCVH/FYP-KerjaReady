import { History } from "lucide-react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/formatDate";

type EarlierAssessmentNoticeProps = {
  // When the shown resume was uploaded, ISO 8601 in UTC
  uploadedAt: string;
};

// Above an assessment that isn't the newest one, with a way back to the latest (mockup 21)
export default function EarlierAssessmentNotice({ uploadedAt }: EarlierAssessmentNoticeProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-4 rounded-xl border bg-card px-6 py-3">
      <p className="flex min-w-0 items-center gap-3 py-2.5 text-sm text-muted-foreground">
        <History aria-hidden="true" className="size-4 shrink-0 text-foreground" />
        <span>
          You’re viewing an earlier assessment from <time dateTime={uploadedAt}>{formatDate(uploadedAt)}</time>.
        </span>
      </p>
      <Button asChild variant="link" className="px-0">
        <Link to="/candidate/resume">View Latest</Link>
      </Button>
    </div>
  );
}
