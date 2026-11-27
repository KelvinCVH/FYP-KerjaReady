import { Check, Circle } from "lucide-react";
import { cn } from "cn";

type StepMarkerProps = {
  // Leave out for the skeleton's placeholder marker
  step?: number;
  // A skill marked done shows a tick on a solid emerald circle instead of its number (KR-99)
  done?: boolean;
};

// A step number in a circle on the skills timeline (the KR-93 pattern: an icon rather than a drawn circle, because
// DESIGN.md keeps round shapes for avatars). Decorative: each card says its step number to screen readers, and its Mark
// as Done button's aria-pressed says whether it is done.
export default function StepMarker({ step, done = false }: StepMarkerProps) {
  return (
    <span aria-hidden="true" className="relative grid size-7 place-items-center">
      <Circle
        className={cn("col-start-1 row-start-1 size-7", done ? "fill-primary text-primary" : "fill-card text-input")}
      />
      {done ? (
        <Check className="col-start-1 row-start-1 size-4 text-primary-foreground" />
      ) : (
        step !== undefined && (
          <span className="col-start-1 row-start-1 text-xs font-semibold tabular-nums">{step}</span>
        )
      )}
    </span>
  );
}
