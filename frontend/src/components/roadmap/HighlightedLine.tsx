import { Fragment } from "react";
import { cn } from "cn";
import { splitPlaceholders } from "@/lib/roadmapText";

type HighlightedLineProps = {
  // An AI-written resume line, such as "Trained a [model type] with [framework]"
  text: string;
  className?: string;
};

// A resume line with each [placeholder] marked, so the candidate sees what to fill in. Plain text only: the line is
// written by AI, so it is never rendered as HTML or markdown.
export default function HighlightedLine({ text, className }: HighlightedLineProps) {
  return (
    <p className={cn("leading-relaxed", className)}>
      {splitPlaceholders(text).map((part, index) =>
        part.placeholder ? (
          <mark key={index} className="rounded-md bg-primary-subtle box-decoration-clone px-1 text-emerald-800">
            {part.text}
          </mark>
        ) : (
          <Fragment key={index}>{part.text}</Fragment>
        ),
      )}
    </p>
  );
}
