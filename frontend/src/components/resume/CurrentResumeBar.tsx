import type { Ref } from "react";
import { FileText } from "lucide-react";
import { profileCard, sectionIconTile } from "@/components/profile/styles";
import { Button } from "@/components/ui/button";

type CurrentResumeBarProps = {
  fileName: string;
  // ISO 8601 in UTC
  uploadedAt: string;
  onUploadNew: () => void;
  uploadNewRef: Ref<HTMLButtonElement>;
};

const dateFormat = new Intl.DateTimeFormat("en-MY", { day: "numeric", month: "short", year: "numeric" });

// The resume the ratings belong to, with Upload New Resume to replace it
export default function CurrentResumeBar({ fileName, uploadedAt, onUploadNew, uploadNewRef }: CurrentResumeBarProps) {
  return (
    <div className={`${profileCard} flex items-center gap-4 py-4`}>
      <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
        <FileText aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-base font-medium break-words">{fileName}</p>
        <p className="text-sm text-muted-foreground tabular-nums">
          Uploaded <time dateTime={uploadedAt}>{dateFormat.format(new Date(uploadedAt))}</time> · Assessed
        </p>
      </div>
      <Button ref={uploadNewRef} type="button" variant="outline" onClick={onUploadNew}>
        Upload New Resume
      </Button>
    </div>
  );
}
