import { useId } from "react";
import { FileText } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatDate } from "@/lib/formatDate";
import type { ResumeSummary } from "@/lib/resumeApi";

type ResumeSelectProps = {
  // Assessed resumes only, newest first
  resumes: ResumeSummary[];
  // The resume shown. It may be missing from resumes when it is older than the ones listed.
  value: number;
  onChange: (resumeId: number) => void;
  // The visible "Resume" label
  labelId: string;
};

const ONLY_ASSESSED = "Only assessed resumes are listed.";

// Picks which assessed resume the skill gap is for (mockup KR-94 resume menu)
export default function ResumeSelect({ resumes, value, onChange, labelId }: ResumeSelectProps) {
  const triggerId = useId();
  const noteId = useId();
  const selected = resumes.find((resume) => resume.resume_id === value);

  return (
    <>
      <Select value={String(value)} onValueChange={(next) => onChange(Number(next))}>
        {/* Named by the label and its own text, so the chosen resume is read with "Resume" */}
        <SelectTrigger id={triggerId} aria-labelledby={`${labelId} ${triggerId}`} aria-describedby={noteId}>
          <SelectValue>
            <FileText aria-hidden="true" className="text-primary" />
            <span className="min-w-0 flex-1 truncate text-left">{selected?.file_name ?? "An earlier resume"}</span>
            {selected && (
              <time dateTime={selected.uploaded_at} className="shrink-0 text-muted-foreground tabular-nums">
                {formatDate(selected.uploaded_at)}
              </time>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent footer={ONLY_ASSESSED}>
          {resumes.map((resume, index) => (
            <SelectItem
              key={resume.resume_id}
              value={String(resume.resume_id)}
              description={`${formatDate(resume.uploaded_at)}${index === 0 ? " · Latest" : ""}`}
            >
              {resume.file_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p id={noteId} className="sr-only">
        {ONLY_ASSESSED}
      </p>
    </>
  );
}
