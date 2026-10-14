import { useEffect, useRef, useState } from "react";
import { CircleCheck } from "lucide-react";
import { inlineLink } from "@/components/auth/authFormClasses";

const RESEND_COOLDOWN_MS = 30_000;

type ResendCodeProps = {
  // Sends a new code. Throw to report a failure through onError.
  onResend: () => Promise<void>;
  // Runs as the request starts, such as clearing an old form error
  onStart?: () => void;
  // Runs after a new code is sent, such as clearing an error about the old code
  onSent?: () => void;
  onError: (error: unknown) => void;
  // Such as "Check your spam folder. The code expires in 1 hour."
  hint: string;
};

// "Didn’t get the code? Resend Code" with a 30 s cooldown and an announced confirmation
export default function ResendCode({ onResend, onStart, onSent, onError, hint }: ResendCodeProps) {
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const [cooldown, setCooldown] = useState(false);
  const cooldownTimer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(cooldownTimer.current), []);

  async function handleResend() {
    if (resending || cooldown) return;

    setResending(true);
    setResent(false);
    onStart?.();
    try {
      await onResend();
      setResending(false);
      setResent(true);
      onSent?.();
      setCooldown(true);
      window.clearTimeout(cooldownTimer.current);
      cooldownTimer.current = window.setTimeout(() => setCooldown(false), RESEND_COOLDOWN_MS);
    } catch (caught) {
      setResending(false);
      onError(caught);
    }
  }

  return (
    <div className="mt-6 text-center text-sm text-pretty text-muted-foreground">
      <p>
        Didn’t get the code?{" "}
        <button
          type="button"
          onClick={handleResend}
          disabled={resending || cooldown}
          className={`font-medium ${inlineLink} disabled:cursor-not-allowed disabled:opacity-50`}
        >
          Resend Code
        </button>
      </p>
      <p className="mt-1">{hint}</p>
      {/* Always rendered so screen readers announce the message when it appears */}
      <p
        aria-live="polite"
        className={resent ? "flex items-center justify-center gap-1.5 pt-1 text-emerald-800" : ""}
      >
        {resent && (
          <>
            <CircleCheck aria-hidden="true" className="size-4" />
            We sent a new code.
          </>
        )}
      </p>
    </div>
  );
}
