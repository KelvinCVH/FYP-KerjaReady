import type { Ref } from "react";
import { CircleAlert } from "lucide-react";

type FormAlertProps = {
  message: string;
  ref?: Ref<HTMLDivElement>;
};

// Error that belongs to the whole form rather than one field (DESIGN.md 5.2 error colours)
export default function FormAlert({ message, ref }: FormAlertProps) {
  return (
    <div
      ref={ref}
      role="alert"
      tabIndex={-1}
      className="flex gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700 outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
    >
      <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <p>{message}</p>
    </div>
  );
}
