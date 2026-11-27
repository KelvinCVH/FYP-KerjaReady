import { useId } from "react";
import { Target } from "lucide-react";
import { cn } from "cn";
import ChangeOnProfileLink from "@/components/profile/ChangeOnProfileLink";
import { profileCard, sectionIconTile } from "@/components/profile/styles";
import { formatDate } from "@/lib/formatDate";
import type { RoadmapResume, RoadmapRole } from "@/lib/roadmapApi";

export type SkillsProgress = { done: number; total: number };

type RoadmapContextCardProps = {
  role: RoadmapRole;
  resume: RoadmapResume;
  // Hidden while the roadmap is being written, because changing the role then would not change this run
  showChangeLink: boolean;
  // How many of this roadmap's skills are marked done (KR-99). Only for a written roadmap with skills to mark.
  progress?: SkillsProgress;
};

// "Skills done", the count and a bar. The bar grows with a transform, which reduced motion makes instant.
function SkillsDone({ done, total }: SkillsProgress) {
  const labelId = useId();

  return (
    <div className="min-w-0 border-t pt-5 sm:col-span-2 xl:col-span-1 xl:border-t-0 xl:pt-0">
      <p id={labelId} className="text-sm text-muted-foreground">
        Skills done
      </p>
      <p className="text-xl font-semibold tabular-nums">
        {done} of {total}
      </p>
      <div
        role="progressbar"
        aria-labelledby={labelId}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={done}
        aria-valuetext={`${done} of ${total}`}
        className="mt-2 h-1.5 overflow-hidden rounded-md bg-muted sm:max-w-md xl:max-w-none"
      >
        <div
          className="h-full origin-left rounded-md bg-primary transition-transform duration-200"
          style={{ transform: `scaleX(${total > 0 ? done / total : 0})` }}
        />
      </div>
    </div>
  );
}

// The target role and the resume the roadmap is written from, and once it is written, how many skills are done.
// Phones stack the parts. With progress, it sits below the other two up to xl and becomes a third column from xl, as
// in the KR-99 mockup.
export default function RoadmapContextCard({ role, resume, showChangeLink, progress }: RoadmapContextCardProps) {
  const postings = role.posting_count;

  return (
    <div
      className={cn(
        `${profileCard} grid gap-x-10 gap-y-5 py-5 sm:grid-cols-2 sm:items-center`,
        progress && "xl:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)_minmax(0,0.85fr)] xl:gap-x-8",
      )}
    >
      <div className="flex min-w-0 items-center gap-4">
        <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
          <Target aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">Target role</p>
          <p className="text-lg font-semibold break-words">{role.title}</p>
          <p className="text-sm text-muted-foreground">
            <span className="tabular-nums">{postings}</span> entry-level job {postings === 1 ? "posting" : "postings"}{" "}
            in Malaysia
            {showChangeLink && (
              <>
                <span aria-hidden="true"> · </span>
                <ChangeOnProfileLink />
              </>
            )}
          </p>
        </div>
      </div>

      <div className="min-w-0 border-t pt-5 sm:border-t-0 sm:pt-0">
        <p className="text-sm text-muted-foreground">Resume</p>
        <p className="font-medium break-words">{resume.file_name}</p>
        <p className="text-sm text-muted-foreground">
          Assessed <time dateTime={resume.assessed_at}>{formatDate(resume.assessed_at)}</time>
        </p>
      </div>

      {progress && <SkillsDone {...progress} />}
    </div>
  );
}
