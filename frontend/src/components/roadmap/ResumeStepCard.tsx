import { ArrowRight } from "lucide-react";
import { profileCard } from "@/components/profile/styles";
import type { ResumeStep } from "@/lib/roadmapApi";
import HighlightedLine from "./HighlightedLine";
import { minorHeading } from "./styles";

// One low-rated assessment criterion: its level now and next, how to reach the next level, and an example line
export default function ResumeStepCard({ step }: { step: ResumeStep }) {
  return (
    <div className={`${profileCard} flex flex-col break-words`}>
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <h3 className="text-base font-semibold break-words">{step.criterion}</h3>
        <p className="shrink-0">
          <span className="sr-only">
            Level now {step.level_label}, next level {step.next_label}
          </span>
          <span
            aria-hidden="true"
            className="inline-flex items-center gap-1 rounded-lg bg-muted px-2 py-0.5 text-sm font-medium"
          >
            {step.level_label}
            <ArrowRight className="size-3.5 shrink-0" />
            <span className="text-emerald-800">{step.next_label}</span>
          </span>
        </p>
      </div>

      <p className="mt-3 text-base leading-relaxed">{step.how_to_improve}</p>

      <div className="mt-4 rounded-lg border bg-background p-4">
        <h4 className={minorHeading}>Example Line</h4>
        <HighlightedLine text={step.example_line} className="mt-1.5 text-base" />
        <p className="mt-2 text-sm text-muted-foreground">Fill in only results you can show.</p>
      </div>

      {step.linked_skills.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-2">
          <p className="text-sm text-muted-foreground">Practise this in</p>
          <ul className="flex flex-wrap gap-2">
            {step.linked_skills.map((skill, index) => (
              <li key={index} className="rounded-lg border px-2 py-0.5 text-sm">
                {skill}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
