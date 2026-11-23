import { ChevronDown } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { EvidencedSkill, MatchMethod } from "@/lib/skillGapApi";
import SkillDemand from "./SkillDemand";

// Said under the resume line when the skill isn't named in it word for word
const MATCH_NOTES: Record<MatchMethod, string | null> = {
  lexical: null,
  implied: "Shown through a related tool in this line",
  semantic: "Close in meaning to this skill",
};

type EvidencedSkillRowProps = {
  skill: EvidencedSkill;
  postingCount: number;
};

// An evidenced skill. Opening the row shows the resume line that evidences it. Closed at first.
export default function EvidencedSkillRow({ skill, postingCount }: EvidencedSkillRowProps) {
  const note = MATCH_NOTES[skill.match_method] ?? null;

  return (
    <Collapsible asChild>
      <li>
        {/* The row touches the card's edges, which clip an outer ring, so the focus ring is inset */}
        <CollapsibleTrigger className="group flex min-h-11 w-full items-center gap-4 px-4 py-2.5 text-left outline-none transition-colors duration-150 hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset">
          <span className="min-w-0 flex-1 text-base break-words">{skill.name}</span>
          <SkillDemand postings={skill.postings} demandShare={skill.demand_share} postingCount={postingCount} />
          <ChevronDown
            aria-hidden="true"
            className="size-4 shrink-0 text-muted-foreground transition-transform duration-150 group-data-[state=open]:rotate-180"
          />
        </CollapsibleTrigger>
        {/* pt-1.5: a gap, so the row's grey hover fill doesn't run into the grey evidence box */}
        <CollapsibleContent className="px-4 pt-1.5 pb-3">
          <div className="rounded-lg bg-muted px-3 py-2.5 text-sm">
            <p className="break-words">“{skill.evidence.trim()}”</p>
            {note && <p className="mt-1 text-muted-foreground">{note}</p>}
          </div>
        </CollapsibleContent>
      </li>
    </Collapsible>
  );
}
