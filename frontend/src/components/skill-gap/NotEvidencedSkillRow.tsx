import { ChevronDown } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { formatMonth } from "@/lib/formatDate";
import type { ExplanationSource, NotEvidencedSkill } from "@/lib/skillGapApi";
import SkillDemand from "./SkillDemand";

const AI_NOTE = "Written with AI from this role's job postings. AI can make mistakes, so check it against other sources.";

type NotEvidencedSkillRowProps = {
  skill: NotEvidencedSkill;
  postingCount: number;
  // Set when other rows in the column have a chevron: a plain row then keeps the same space, so the numbers line up
  alignWithChevrons?: boolean;
};

// The job posting lines an explanation is based on, behind their own toggle. Closed at first.
function SourcePostings({ sources }: { sources: ExplanationSource[] }) {
  const one = sources.length === 1;
  return (
    <Collapsible>
      {/* Inside the panel, not the row's button, so no button sits inside another */}
      <CollapsibleTrigger className="group/sources mt-1 inline-flex min-h-11 items-center gap-1.5 rounded-md font-medium text-primary outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-muted">
        <span className="group-data-[state=open]/sources:hidden">
          {one ? "Show 1 Source Posting" : `Show ${sources.length} Source Postings`}
        </span>
        <span className="hidden group-data-[state=open]/sources:inline">
          {one ? "Hide Source Posting" : "Hide Source Postings"}
        </span>
        <ChevronDown
          aria-hidden="true"
          className="size-4 shrink-0 transition-transform duration-150 group-data-[state=open]/sources:rotate-180"
        />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ul className="space-y-3 pt-1 pb-1">
          {sources.map((source) => (
            <li key={source.posting_id}>
              <p className="break-words">“{source.line.trim()}”</p>
              <p className="mt-0.5 text-muted-foreground">
                {source.job_title} ·{" "}
                <time dateTime={source.posted_date} className="whitespace-nowrap">
                  {formatMonth(source.posted_date)}
                </time>
              </p>
            </li>
          ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  );
}

// A skill not evidenced in the resume. With an explanation, opening the row shows why the role asks for it, how to
// show it, an AI note and the source postings; closed at first. Without one, it stays a plain row.
export default function NotEvidencedSkillRow({ skill, postingCount, alignWithChevrons = false }: NotEvidencedSkillRowProps) {
  const demand = <SkillDemand postings={skill.postings} demandShare={skill.demand_share} postingCount={postingCount} />;

  // An older API without the fields counts as no explanation
  if (!skill.why_it_matters) {
    return (
      <li className="flex min-h-11 items-center gap-4 px-4 py-2.5">
        <span className="min-w-0 flex-1 text-base break-words">{skill.name}</span>
        {demand}
        {alignWithChevrons && <span aria-hidden="true" className="size-4 shrink-0" />}
      </li>
    );
  }

  const sources = skill.sources ?? [];
  return (
    <Collapsible asChild>
      <li>
        {/* Same row as an evidenced skill: the card's edges clip an outer ring, so the focus ring is inset */}
        <CollapsibleTrigger className="group flex min-h-11 w-full items-center gap-4 px-4 py-2.5 text-left outline-none transition-colors duration-150 hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset">
          <span className="min-w-0 flex-1 text-base break-words">{skill.name}</span>
          {demand}
          <ChevronDown
            aria-hidden="true"
            className="size-4 shrink-0 text-muted-foreground transition-transform duration-150 group-data-[state=open]:rotate-180"
          />
        </CollapsibleTrigger>
        {/* pt-1.5: a gap, so the row's grey hover fill doesn't run into the grey panel */}
        <CollapsibleContent className="px-4 pt-1.5 pb-3">
          <div className="rounded-lg bg-muted px-3 py-3 text-sm leading-relaxed">
            <h3 className="font-semibold">Why It Matters</h3>
            <p className="mt-0.5 break-words">{skill.why_it_matters}</p>
            {skill.how_to_show && (
              <>
                <h3 className="mt-3 font-semibold">How to Show It</h3>
                <p className="mt-0.5 break-words">{skill.how_to_show}</p>
              </>
            )}
            <div className="mt-3 border-t pt-3">
              <p className="text-muted-foreground">{AI_NOTE}</p>
              {sources.length > 0 && <SourcePostings sources={sources} />}
            </div>
          </div>
        </CollapsibleContent>
      </li>
    </Collapsible>
  );
}
