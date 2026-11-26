import { Target } from "lucide-react";
import ChangeOnProfileLink from "@/components/profile/ChangeOnProfileLink";
import { profileCard, sectionIconTile } from "@/components/profile/styles";
import { formatDate } from "@/lib/formatDate";
import type { RoadmapResume, RoadmapRole } from "@/lib/roadmapApi";

type RoadmapContextCardProps = {
  role: RoadmapRole;
  resume: RoadmapResume;
  // Hidden while the roadmap is being written, because changing the role then would not change this run
  showChangeLink: boolean;
};

// The target role and the resume the roadmap is written from. The two halves stack on phones.
export default function RoadmapContextCard({ role, resume, showChangeLink }: RoadmapContextCardProps) {
  const postings = role.posting_count;

  return (
    <div className={`${profileCard} grid gap-x-10 gap-y-5 py-5 sm:grid-cols-2 sm:items-center`}>
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
    </div>
  );
}
