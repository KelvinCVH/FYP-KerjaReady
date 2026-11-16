import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { sectionIconTile } from "@/components/profile/styles";
import { formatFileSize } from "@/lib/resumeFile";

type SelectedResumeFileProps = {
  file: File;
  uploaded: boolean;
  // Opens the file picker. Change File is hidden once the resume is uploaded.
  onChange: () => void;
  changeDisabled: boolean;
};

// The chosen PDF's name and size, with Change File to pick another one
export default function SelectedResumeFile({ file, uploaded, onChange, changeDisabled }: SelectedResumeFileProps) {
  const size = formatFileSize(file.size);

  return (
    <div className="flex items-center gap-4 rounded-xl border p-4">
      <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
        <FileText aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-base font-medium break-words">{file.name}</p>
        <p className="text-sm text-muted-foreground tabular-nums">{uploaded ? `${size} · Uploaded` : size}</p>
      </div>
      {!uploaded && (
        <Button type="button" variant="outline" disabled={changeDisabled} onClick={onChange}>
          Change File
        </Button>
      )}
    </div>
  );
}
