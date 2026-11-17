import { useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { profileCard } from "@/components/profile/styles";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { RubricCriterion } from "@/lib/rubric";
import LevelIndicator from "./LevelIndicator";

type CriterionCardProps = {
  criterion: RubricCriterion;
  // 0 to 3, already checked by the page
  level: number;
  // Evidence the checker found, shown under the level's meaning
  children?: ReactNode;
};

// One rubric criterion with its level. The header is a button that collapses the details, so a long page can be
// scanned by level alone. Cards start open, and the choice is not remembered.
export default function CriterionCard({ criterion, level, children }: CriterionCardProps) {
  const [open, setOpen] = useState(true);
  const current = criterion.levels[level];
  // Only below level 3, and only where the rubric says what the next level needs
  const next = level < 3 && current.nextLevel !== null ? { label: criterion.levels[level + 1].label, text: current.nextLevel } : null;
  // Names the card region by the criterion alone; the button inside also reads out the level
  const headingId = `criterion-${criterion.key}-name`;

  return (
    <Collapsible asChild open={open} onOpenChange={setOpen}>
      <section aria-labelledby={headingId} className={profileCard}>
        {/* Pulled out by the button's padding, so the hover area has room while the text lines up with the card */}
        <h3 className="-m-2 text-base font-semibold">
          <CollapsibleTrigger className="group flex w-full items-start gap-4 rounded-lg p-2 text-left outline-none hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card">
            <span id={headingId} className="min-w-0 flex-1 text-balance">
              {criterion.name}
            </span>
            <LevelIndicator level={level} label={current.label} />
            <ChevronDown
              aria-hidden="true"
              className="mt-0.5 size-4 shrink-0 text-muted-foreground transition-transform duration-150 group-data-[state=open]:rotate-180"
            />
          </CollapsibleTrigger>
        </h3>

        <CollapsibleContent className="mt-2 space-y-4">
          <div>
            <p className="max-w-[65ch] text-sm text-muted-foreground">{criterion.question}</p>
            <p className="mt-4 max-w-[65ch] text-sm leading-relaxed">{current.meaning}</p>
          </div>

          {next && (
            <div className="rounded-xl border bg-background px-4 py-3">
              <p className="text-sm font-semibold">Next level: {next.label}</p>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{next.text}</p>
            </div>
          )}

          {children}
        </CollapsibleContent>
      </section>
    </Collapsible>
  );
}
