import type { ComponentProps } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type CodeInputProps = Omit<ComponentProps<"input">, "value" | "onChange"> & {
  value: string;
  // Receives the value with spaces removed, so a pasted "123 456" still works
  onValueChange: (value: string) => void;
};

// 6-digit email code field (Verify Email, Reset Password)
export default function CodeInput({ value, onValueChange, className, ...props }: CodeInputProps) {
  return (
    <Input
      inputMode="numeric"
      autoComplete="one-time-code"
      spellCheck={false}
      placeholder="000000"
      {...props}
      value={value}
      onChange={(event) => onValueChange(event.target.value.replace(/\s/g, ""))}
      className={cn("text-center font-mono text-lg tracking-[0.4em] tabular-nums", className)}
    />
  );
}
