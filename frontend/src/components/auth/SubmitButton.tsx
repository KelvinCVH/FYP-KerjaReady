import type { ReactNode } from "react";
import { LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

type SubmitButtonProps = {
  pending: boolean;
  // Announced to screen readers while the request runs, such as "Creating account…"
  pendingLabel: string;
  children: ReactNode;
};

// Full-width primary submit. While pending it is disabled and shows a spinner beside the same label.
export default function SubmitButton({ pending, pendingLabel, children }: SubmitButtonProps) {
  return (
    <>
      {/* Before the button so the button stays the last child in space-y layouts */}
      <span role="status" className="sr-only">
        {pending ? pendingLabel : ""}
      </span>
      <Button type="submit" disabled={pending} className="w-full">
        {pending && <LoaderCircle aria-hidden="true" className="animate-spin" />}
        {children}
      </Button>
    </>
  );
}
