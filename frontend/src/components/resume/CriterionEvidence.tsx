import { LinkIcon } from "lucide-react";
import type { LanguageError } from "@/lib/resumeApi";
import { toWorkLink } from "@/lib/workLink";

// Work Evidence: the link to the candidate's work that the checker found in the resume
export function WorkLinkEvidence({ link }: { link: string }) {
  const { display, href } = toWorkLink(link);

  return (
    <p className="flex items-start gap-2 text-sm text-muted-foreground">
      <LinkIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <span className="min-w-0">
        Link to your work found in your resume:{" "}
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md font-medium break-all text-primary underline underline-offset-2 outline-none hover:text-primary-hover focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
          >
            {display}
            <span className="sr-only"> (opens in a new tab)</span>
          </a>
        ) : (
          <span className="font-medium break-all text-foreground">{display}</span>
        )}
      </span>
    </p>
  );
}

// Language Quality: each error the checker found. Dark text, not red: red is only for system and
// form errors, never for assessment results (DESIGN.md 5.3).
export function LanguageErrorList({ errors, headingId }: { errors: LanguageError[]; headingId: string }) {
  return (
    <div>
      <h4 id={headingId} className="text-sm font-semibold">
        Errors found
      </h4>
      <ul aria-labelledby={headingId} className="mt-2 divide-y rounded-lg border">
        {errors.map((error, index) => (
          <li key={index} className="flex flex-wrap gap-x-3 gap-y-1 px-4 py-3 text-sm">
            <span className="font-medium break-words text-foreground">“{error.text}”</span>
            <span className="min-w-0 text-muted-foreground">{error.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
