import { ArrowRight, Check, ChevronDown } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import type { SkillMilestone } from "@/lib/roadmapApi";
import { postingPercent } from "@/lib/roadmapText";
import SkillTile from "./SkillTile";
import { minorHeading } from "./styles";

type SkillCardProps = {
  milestone: SkillMilestone;
  // 1-based position in demand order
  step: number;
  selected: boolean;
  // The details panel, which exists only while this card is selected
  panelId: string;
  buttonId: string;
  onToggle: () => void;
  // Marks the skill done, or undoes it (KR-99)
  onToggleDone: () => void;
};

// One skill to build. Selected, it has a dark border (and a dark letter tile) and its button reads Hide Details, so
// the state doesn't rely on colour alone. Done, its Mark as Done button reads Done, with an emerald border and
// aria-pressed. A skill no longer in the role profile has no skill_id, so it can't be marked and has no button.
export default function SkillCard({
  milestone,
  step,
  selected,
  panelId,
  buttonId,
  onToggle,
  onToggleDone,
}: SkillCardProps) {
  const { skill, postings, done } = milestone;
  const percent = postingPercent(postings, milestone.role_postings);

  return (
    <div
      className={cn(
        // break-words: AI text can hold a long unbroken token, such as a URL
        "flex flex-1 flex-col rounded-xl border-2 p-4 break-words",
        selected ? "border-zinc-600 bg-muted" : "border-border bg-card",
      )}
    >
      <div className="flex items-start gap-3">
        <SkillTile skill={skill} selected={selected} />
        <div className="min-w-0">
          <h3 className="text-base font-semibold break-words">
            <span className="sr-only">Step {step}: </span>
            {skill}
          </h3>
          <p className="text-sm text-muted-foreground">
            Asked in{" "}
            <span className="tabular-nums">
              {postings} ({percent}%)
            </span>{" "}
            {postings === 1 ? "posting" : "postings"}
          </p>
        </div>
      </div>

      {milestone.learn_after && (
        <p className="mt-3 flex items-start gap-1.5 text-sm font-medium">
          <ArrowRight aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          <span className="min-w-0 break-words">Learn after {milestone.learn_after}</span>
        </p>
      )}

      {milestone.why_it_matters && (
        <div className="mt-4">
          <h4 className={minorHeading}>Why It Matters</h4>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{milestone.why_it_matters}</p>
        </div>
      )}

      {milestone.prerequisites && (
        <div className="mt-4">
          <h4 className={minorHeading}>Prerequisites</h4>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{milestone.prerequisites}</p>
        </div>
      )}

      <div className="mt-auto flex flex-col gap-2 pt-5">
        {milestone.skill_id !== null && (
          <Button
            variant="outline"
            className={cn("w-full", done && "border-2 border-primary text-primary")}
            aria-pressed={done}
            onClick={onToggleDone}
          >
            <Check aria-hidden="true" className="size-4" />
            <span>
              {done ? "Done" : "Mark as Done"}
              <span className="sr-only"> for {skill}</span>
            </span>
          </Button>
        )}
        <Button
          id={buttonId}
          variant="outline"
          className={cn("w-full", !selected && "text-primary")}
          aria-expanded={selected}
          aria-controls={selected ? panelId : undefined}
          onClick={onToggle}
        >
          <span>
            {selected ? "Hide Details" : "View Details"}
            <span className="sr-only"> for {skill}</span>
          </span>
          <ChevronDown
            aria-hidden="true"
            className={cn("size-4 transition-transform duration-150", selected && "rotate-180")}
          />
        </Button>
      </div>
    </div>
  );
}
