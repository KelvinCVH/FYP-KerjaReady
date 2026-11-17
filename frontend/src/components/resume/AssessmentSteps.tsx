import { Circle, CircleCheck, LoaderCircle } from "lucide-react";
import { cn } from "cn";
import type { AssessmentStatus } from "@/lib/resumeApi";

const STEPS = [
  { label: "Uploaded", description: "Your PDF is saved." },
  { label: "Reading resume", description: "Taking out the text and links from your PDF." },
  { label: "Rating", description: "Rating work evidence, outcomes, skills in use and language quality." },
  { label: "Done", description: "Your ratings appear on this page." },
];

// The step in progress for each running status. done is past the last step, so every step is ticked.
const ACTIVE_STEP: Partial<Record<AssessmentStatus, number>> = { uploaded: 1, reading: 1, rating: 2, done: 4 };

type StepState = "done" | "active" | "waiting";

function StepMarker({ state }: { state: StepState }) {
  // Icons rather than drawn circles: DESIGN.md keeps round shapes for avatars
  if (state === "done") return <CircleCheck aria-hidden="true" className="size-7 fill-primary text-primary-foreground" />;
  if (state === "waiting") return <Circle aria-hidden="true" className="size-7 text-input" />;
  return (
    <span aria-hidden="true" className="relative grid size-7 place-items-center">
      <Circle className="col-start-1 row-start-1 size-7 text-primary" />
      <LoaderCircle className="col-start-1 row-start-1 size-3.5 animate-spin text-primary" />
    </span>
  );
}

// The four stages, with the one in progress marked. "Starting…" while the run has not begun reading.
export default function AssessmentSteps({ status }: { status: AssessmentStatus }) {
  const active = ACTIVE_STEP[status] ?? 0;
  const activeText = status === "uploaded" ? "Starting…" : "In progress";

  return (
    <ol className="mt-5 border-t pt-6">
      {STEPS.map((step, index) => {
        const state: StepState = index < active ? "done" : index === active ? "active" : "waiting";
        const isLast = index === STEPS.length - 1;
        return (
          <li
            key={step.label}
            aria-current={state === "active" ? "step" : undefined}
            className={cn("relative flex gap-4", !isLast && "pb-5")}
          >
            {!isLast && (
              // Connector to the next step: emerald once that step has been reached
              <span
                aria-hidden="true"
                className={cn("absolute top-7 bottom-0 left-[13px] w-0.5", index < active ? "bg-primary" : "bg-border")}
              />
            )}
            <StepMarker state={state} />
            <div className="min-w-0 flex-1 pt-0.5">
              <p
                className={cn(
                  "text-base",
                  state === "done" && "font-medium",
                  state === "active" && "font-semibold",
                  state === "waiting" && "font-medium text-muted-foreground",
                )}
              >
                {step.label}
              </p>
              <p className="text-sm text-muted-foreground">{step.description}</p>
            </div>
            <p
              className={cn(
                "shrink-0 pt-0.5 text-sm",
                state === "active" ? "font-medium text-primary" : "text-muted-foreground",
              )}
            >
              {state === "done" ? "Done" : state === "active" ? activeText : "Waiting"}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
