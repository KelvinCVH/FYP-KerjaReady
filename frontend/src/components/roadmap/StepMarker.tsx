import { Circle } from "lucide-react";

// A step number in a circle on the skills timeline (the KR-93 pattern: an icon rather than a drawn circle, because
// DESIGN.md keeps round shapes for avatars). Without a number it is a placeholder for the skeleton. Decorative: each
// card says its step number to screen readers.
export default function StepMarker({ step }: { step?: number }) {
  return (
    <span aria-hidden="true" className="relative grid size-7 place-items-center">
      <Circle className="col-start-1 row-start-1 size-7 fill-card text-input" />
      {step !== undefined && (
        <span className="col-start-1 row-start-1 text-xs font-semibold tabular-nums">{step}</span>
      )}
    </span>
  );
}
