import type { ComponentProps, MouseEvent } from "react";
import { cn } from "cn";
import { LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

type LoadingButtonProps = ComponentProps<typeof Button> & {
  pending: boolean;
  // Replaces the label while the request runs, such as "Saving…"
  pendingLabel: string;
};

// While pending, shows a spinner and pendingLabel at the width of the normal label (DESIGN.md 9.1).
// It uses aria-disabled rather than disabled, so a keyboard user keeps focus on it, and ignores clicks.
export default function LoadingButton({
  pending,
  pendingLabel,
  children,
  onClick,
  className,
  ...props
}: LoadingButtonProps) {
  function handleClick(event: MouseEvent<HTMLButtonElement>) {
    if (pending) {
      event.preventDefault();
      return;
    }
    onClick?.(event);
  }

  return (
    <Button
      {...props}
      aria-disabled={pending || undefined}
      onClick={handleClick}
      className={cn(pending && "pointer-events-none", className)}
    >
      {/* Both labels share one grid cell, so the wider one sets the width */}
      <span className="grid">
        <span className={cn("col-start-1 row-start-1", pending && "invisible")}>{children}</span>
        <span
          aria-hidden={!pending}
          className={cn(
            "col-start-1 row-start-1 inline-flex items-center justify-center gap-2",
            !pending && "invisible",
          )}
        >
          <LoaderCircle aria-hidden="true" className="animate-spin" />
          {pendingLabel}
        </span>
      </span>
    </Button>
  );
}
