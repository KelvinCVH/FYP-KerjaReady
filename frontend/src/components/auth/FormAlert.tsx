import type { Ref } from "react";
import { CircleAlert, CircleCheck } from "lucide-react";

type FormAlertProps = {
  message: string;
  // "error" for a failure, "success" for a confirmation such as a completed password reset
  variant?: "error" | "success";
  ref?: Ref<HTMLDivElement>;
};

const variants = {
  error: { className: "border-red-200 bg-red-50 text-red-700", Icon: CircleAlert, role: "alert" },
  success: {
    className: "border-emerald-200 bg-emerald-50 text-emerald-800",
    Icon: CircleCheck,
    role: "status",
  },
} as const;

// Message that belongs to the whole form rather than one field (DESIGN.md 5.2 status colours)
export default function FormAlert({ message, variant = "error", ref }: FormAlertProps) {
  const { className, Icon, role } = variants[variant];

  return (
    <div
      ref={ref}
      role={role}
      tabIndex={-1}
      className={`flex gap-3 rounded-lg border px-4 py-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card ${className}`}
    >
      <Icon aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <p>{message}</p>
    </div>
  );
}
