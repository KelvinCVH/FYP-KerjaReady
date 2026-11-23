import { useId, useState } from "react";
import { ChevronDown, CircleCheck, CircleDashed } from "lucide-react";
import { cn } from "cn";
import { Badge } from "@/components/ui/badge";
import type { EvidencedSkill, SkillDemand as Demand } from "@/lib/skillGapApi";
import EvidencedSkillRow from "./EvidencedSkillRow";
import SkillDemand from "./SkillDemand";

// Rows shown before Show All
const VISIBLE_ROWS = 8;

const COPY = {
  not_evidenced: {
    heading: "Not Evidenced in Your Resume",
    helper: "If you have any of these skills, show them in your resume with what you built using them.",
    empty: "Every skill for this role is evidenced in this resume.",
  },
  evidenced: {
    heading: "Evidenced in Your Resume",
    helper: "Select a skill to see the resume line that evidences it.",
    empty: "None of this role’s skills are evidenced in this resume yet.",
  },
};

type SkillColumnProps = { postingCount: number } & (
  | { kind: "not_evidenced"; skills: Demand[] }
  | { kind: "evidenced"; skills: EvidencedSkill[] }
);

// One side of the skill gap, in demand order, with the first 8 rows and Show All for the rest.
// The page remounts it for each resume, so Show All and open rows start closed again.
export default function SkillColumn(props: SkillColumnProps) {
  const { kind, postingCount } = props;
  const [showAll, setShowAll] = useState(false);
  const headingId = useId();
  const listId = useId();
  const copy = COPY[kind];
  const count = props.skills.length;
  const shown = showAll ? count : VISIBLE_ROWS;
  const Icon = kind === "evidenced" ? CircleCheck : CircleDashed;

  const rows =
    props.kind === "evidenced"
      ? props.skills
          .slice(0, shown)
          .map((skill) => <EvidencedSkillRow key={skill.skill_id} skill={skill} postingCount={postingCount} />)
      : props.skills.slice(0, shown).map((skill) => (
          <li key={skill.skill_id} className="flex min-h-11 items-center justify-between gap-4 px-4 py-2.5">
            <span className="min-w-0 text-base break-words">{skill.name}</span>
            <SkillDemand postings={skill.postings} demandShare={skill.demand_share} postingCount={postingCount} />
          </li>
        ));

  return (
    <section aria-labelledby={headingId} className="overflow-hidden rounded-xl border bg-card">
      <div className="p-4">
        <h2 id={headingId} className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xl font-semibold text-balance">
          {/* DESIGN.md 5.2: zinc-700 CircleDashed for not evidenced, emerald-800 CircleCheck for evidenced */}
          <Icon
            aria-hidden="true"
            className={cn("size-5 shrink-0", kind === "evidenced" ? "text-emerald-800" : "text-zinc-700")}
          />
          {copy.heading}
          <Badge variant="neutral" className="tabular-nums">
            {count}
            <span className="sr-only"> {count === 1 ? "skill" : "skills"}</span>
          </Badge>
        </h2>
        {count > 0 && <p className="mt-1 text-sm text-muted-foreground">{copy.helper}</p>}
      </div>

      {count === 0 ? (
        <p className="border-t px-4 py-4 text-sm text-muted-foreground">{copy.empty}</p>
      ) : (
        <>
          {/* Column titles for sighted users; every row also says what its numbers mean to screen readers */}
          <div
            aria-hidden="true"
            className="flex justify-between gap-4 border-y bg-background px-4 py-2 text-sm text-muted-foreground"
          >
            <span>Skill</span>
            <span>Asked in postings (of {postingCount})</span>
          </div>
          <ul id={listId} className="divide-y">
            {rows}
          </ul>
          {count > VISIBLE_ROWS && (
            <button
              type="button"
              aria-expanded={showAll}
              aria-controls={listId}
              onClick={() => setShowAll((open) => !open)}
              className="flex min-h-11 w-full items-center justify-center gap-1.5 border-t bg-background text-sm font-medium text-primary outline-none transition-colors duration-150 hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
            >
              {showAll ? "Show Fewer Skills" : `Show All ${count} Skills`}
              <ChevronDown
                aria-hidden="true"
                className={cn("size-4 transition-transform duration-150", showAll && "rotate-180")}
              />
            </button>
          )}
        </>
      )}
    </section>
  );
}
