import type { ReactNode } from "react";
import FieldError from "@/components/auth/FieldError";
import { Label } from "@/components/ui/label";

type FormFieldProps = {
  id: string;
  label: string;
  error?: ReactNode;
  helper?: string;
  // Shown at the end of the label row, such as a "Forgot Password?" link
  labelAside?: ReactNode;
  // Receives the aria props to spread on the control
  children: (aria: { "aria-invalid"?: true; "aria-describedby"?: string }) => ReactNode;
};

// Label above the control, then the error, then the helper text (DESIGN.md 9.2)
export default function FormField({ id, label, error, helper, labelAside, children }: FormFieldProps) {
  const errorId = `${id}-error`;
  const helperId = `${id}-helper`;
  const describedBy = [error && errorId, helper && helperId].filter(Boolean).join(" ");

  return (
    <div className="space-y-2">
      {labelAside ? (
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor={id}>{label}</Label>
          {labelAside}
        </div>
      ) : (
        <Label htmlFor={id}>{label}</Label>
      )}
      {children({
        "aria-invalid": error ? true : undefined,
        "aria-describedby": describedBy || undefined,
      })}
      {error && <FieldError id={errorId}>{error}</FieldError>}
      {helper && (
        <p id={helperId} className="text-sm text-muted-foreground">
          {helper}
        </p>
      )}
    </div>
  );
}
