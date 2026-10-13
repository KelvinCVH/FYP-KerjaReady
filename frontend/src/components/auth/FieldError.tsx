import type { ReactNode } from "react";
import { CircleAlert } from "lucide-react";

type FieldErrorProps = {
  id: string;
  children: ReactNode;
};

// Error text under a form field. Link it to the field with aria-describedby.
export default function FieldError({ id, children }: FieldErrorProps) {
  return (
    <p id={id} className="flex gap-2 text-sm text-destructive">
      <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <span>{children}</span>
    </p>
  );
}
