import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { sectionIconTile } from "@/components/profile/styles";
import { formatFileSize } from "@/lib/resumeFile";

type SelectedResumeFileProps = {
  name: string;
  // In bytes. Unknown for a resume uploaded before the page loaded, which shows only "Uploaded".
  size?: number;
  uploaded: boolean;
  // Opens the file picker. Change File is hidden once the resume is uploaded.
  onChange?: () => void;
  changeDisabled?: boolean;
};

// The chosen PDF's name and size, with Change File to pick another one
export default function SelectedResumeFile({ name, size, uploaded, onChange, changeDisabled }: SelectedResumeFileProps) {
  const sizeText = size === undefined ? null : formatFileSize(size);
  const caption = uploaded ? [sizeText, "Uploaded"].filter(Boolean).join(" · ") : sizeText;

  return (
    <div className="flex items-center gap-4 rounded-xl border p-4">
      <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
        <FileText aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-base font-medium break-words">{name}</p>
        <p className="text-sm text-muted-foreground tabular-nums">{caption}</p>
      </div>
      {!uploaded && onChange && (
        <Button type="button" variant="outline" disabled={changeDisabled} onClick={onChange}>
          Change File
        </Button>
      )}
    </div>
  );
}
