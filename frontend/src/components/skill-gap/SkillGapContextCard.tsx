import { useId } from "react";
import { Link } from "react-router";
import { Target } from "lucide-react";
import { profileCard, sectionIconTile } from "@/components/profile/styles";
import { Skeleton } from "@/components/ui/skeleton";
import type { ResumeSummary } from "@/lib/resumeApi";
import type { SkillGapRole } from "@/lib/skillGapApi";
import ResumeSelect from "./ResumeSelect";

// "loading" while the selected resume's skill gap loads; null when it failed, so nothing from another resume shows
export type SkillCounts = { evidenced: number; total: number } | "loading" | null;

type SkillGapContextCardProps = {
  targetRole: SkillGapRole;
  counts: SkillCounts;
  // Assessed resumes, newest first
  resumes: ResumeSummary[];
  selectedId: number;
  onSelect: (resumeId: number) => void;
};

// One row above the columns: the saved target role, how many of its skills are evidenced, and the resume compared
export default function SkillGapContextCard({
  targetRole,
  counts,
  resumes,
  selectedId,
  onSelect,
}: SkillGapContextCardProps) {
  const resumeLabelId = useId();
  const postings = targetRole.posting_count;
  const showCounts = counts === "loading" || (counts !== null && counts.total > 0);

  return (
    <div
      className={`${profileCard} grid gap-x-10 gap-y-5 py-5 sm:grid-cols-[minmax(0,1fr)_auto] lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,22rem)] lg:items-center`}
    >
      <div className="flex min-w-0 items-center gap-4">
        <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
          <Target aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">Target role</p>
          <p className="text-lg font-semibold break-words">{targetRole.title}</p>
          <p className="text-sm text-muted-foreground">
            <span className="tabular-nums">{postings}</span> entry-level {postings === 1 ? "posting" : "postings"} in
            Malaysia<span aria-hidden="true"> · </span>
            {/* The ::before box makes the touch target 44px tall without changing the line */}
            <Link
              to="/candidate/profile"
              className="relative rounded-md font-medium text-primary underline-offset-4 outline-none before:absolute before:-inset-x-1 before:-inset-y-3.5 before:content-[''] hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
            >
              Change on Profile
            </Link>
          </p>
        </div>
      </div>

      {/* Kept as an empty cell when hidden, so the resume selector stays in its column */}
      <div>
        {showCounts && (
          <>
            <p className="text-sm text-muted-foreground">Skills evidenced</p>
            {counts === "loading" ? (
              <Skeleton aria-hidden="true" className="mt-1 h-8 w-20" />
            ) : (
              <p className="text-2xl font-semibold tabular-nums">
                {counts?.evidenced} of {counts?.total}
              </p>
            )}
          </>
        )}
      </div>

      <div className="min-w-0 sm:col-span-2 lg:col-span-1">
        <p id={resumeLabelId} className="mb-1.5 text-sm text-muted-foreground">
          Resume
        </p>
        <ResumeSelect resumes={resumes} value={selectedId} onChange={onSelect} labelId={resumeLabelId} />
      </div>
    </div>
  );
}
