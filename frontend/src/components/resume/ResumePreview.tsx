import { ExternalLink } from "lucide-react";
import { profileCard } from "@/components/profile/styles";

// The uploaded PDF in the browser's own viewer, so no PDF library is needed. The link is valid for an hour;
// reloading the page gets a new one.
export default function ResumePreview({ url }: { url: string }) {
  return (
    <section aria-labelledby="resume-preview-heading" className={`${profileCard} min-w-0 self-start`}>
      <div className="flex items-center justify-between gap-4">
        <h2 id="resume-preview-heading" className="text-xl font-semibold text-balance">
          Your Resume
        </h2>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex shrink-0 items-center gap-1.5 rounded-md text-sm font-medium text-primary outline-none hover:text-primary-hover hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
        >
          Open in New Tab
          <ExternalLink aria-hidden="true" className="size-4" />
        </a>
      </div>
      <iframe src={url} title="Your resume (PDF)" className="mt-6 h-240 w-full rounded-lg border bg-muted" />
      <p className="mt-3 text-sm text-muted-foreground">Shown in your browser’s PDF viewer.</p>
    </section>
  );
}
