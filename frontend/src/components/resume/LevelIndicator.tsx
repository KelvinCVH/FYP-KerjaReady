import { cn } from "cn";

type LevelIndicatorProps = {
  // 0 to 3
  level: number;
  label: string;
};

const SEGMENTS = [1, 2, 3];

// Three segments plus the level written out, so colour is never the only signal (DESIGN.md 5.2).
// The segments repeat the text, so they are hidden from screen readers.
export default function LevelIndicator({ level, label }: LevelIndicatorProps) {
  return (
    <span className="flex shrink-0 items-center gap-2.5">
      <span aria-hidden="true" className="flex gap-1">
        {SEGMENTS.map((segment) => (
          <span key={segment} className={cn("h-1 w-6 rounded-md", segment <= level ? "bg-primary" : "bg-muted")} />
        ))}
      </span>
      <span className="text-sm font-medium whitespace-nowrap tabular-nums">
        <span className="sr-only">Rating: </span>
        {label} · {level} of 3
      </span>
    </span>
  );
}
