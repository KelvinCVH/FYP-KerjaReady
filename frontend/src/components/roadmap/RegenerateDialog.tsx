import { useState, type Ref } from "react";
import { RefreshCw } from "lucide-react";
import LoadingButton from "@/components/LoadingButton";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

type RegenerateDialogProps = {
  // The Regenerate Roadmap button, so the page can return focus to it when a new run can't start
  triggerRef: Ref<HTMLButtonElement>;
  // A run is starting: the button shows "Starting…" and ignores clicks
  starting: boolean;
  onConfirm: () => void;
};

// The Regenerate Roadmap button and its confirmation, because a new run replaces the roadmap on screen.
// Closing returns focus to the button, which shows "Starting…" until the new run starts or fails.
export default function RegenerateDialog({ triggerRef, starting, onConfirm }: RegenerateDialogProps) {
  const [open, setOpen] = useState(false);

  function confirm() {
    setOpen(false);
    onConfirm();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <LoadingButton ref={triggerRef} variant="outline" pending={starting} pendingLabel="Starting…">
          <span className="inline-flex items-center gap-2">
            <RefreshCw aria-hidden="true" className="size-4" />
            Regenerate Roadmap
          </span>
        </LoadingButton>
      </DialogTrigger>
      <DialogContent showCloseButton={false}>
        <DialogHeader className="pr-0">
          <DialogTitle>Regenerate Roadmap?</DialogTitle>
          <DialogDescription>This writes a new roadmap for your latest resume and target role.</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button onClick={confirm}>Regenerate</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
