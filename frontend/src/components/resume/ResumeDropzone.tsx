import { useState, type DragEvent, type Ref } from "react";
import { cn } from "cn";
import { FileUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { sectionIconTile } from "@/components/profile/styles";

type ResumeDropzoneProps = {
  // Called with the dropped file. Validation happens in the page, the same as for a picked file.
  onDrop: (file: File) => void;
  // Opens the file picker
  onChoose: () => void;
  // The helper text that describes the Choose PDF button
  describedBy: string;
  chooseRef: Ref<HTMLButtonElement>;
};

// Dashed area to drop a PDF on, with Choose PDF for keyboard and touch users
export default function ResumeDropzone({ onDrop, onChoose, describedBy, chooseRef }: ResumeDropzoneProps) {
  const [dragging, setDragging] = useState(false);

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    // Without preventDefault the browser opens the file instead of dropping it here
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setDragging(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    // Moving over a child element also fires dragleave, so only reset when the pointer leaves the area
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) onDrop(file);
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        // No colour transition: DESIGN.md 12 animates transform and opacity only
        "flex flex-col items-center rounded-xl border border-dashed bg-background px-6 py-10 text-center",
        dragging ? "border-primary" : "border-input/40",
      )}
    >
      <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
        <FileUp aria-hidden="true" />
      </div>
      <p className="mt-4 text-base font-semibold">Drag and drop your PDF here</p>
      <p className="mt-1 text-sm text-muted-foreground">or choose it from your device</p>
      <Button ref={chooseRef} type="button" className="mt-4" aria-describedby={describedBy} onClick={onChoose}>
        Choose PDF
      </Button>
    </div>
  );
}
