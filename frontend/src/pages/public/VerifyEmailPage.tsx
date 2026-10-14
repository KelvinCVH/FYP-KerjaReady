import { useEffect, useRef, useState, type FormEvent } from "react";
import { flushSync } from "react-dom";
import { Link, Navigate, useLocation } from "react-router";
import { confirmSignUp, resendSignUpCode } from "aws-amplify/auth";
import { Check, Mail } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import CodeInput from "@/components/auth/CodeInput";
import FieldError from "@/components/auth/FieldError";
import FormAlert from "@/components/auth/FormAlert";
import ResendCode from "@/components/auth/ResendCode";
import SubmitButton from "@/components/auth/SubmitButton";
import { iconTile, quietLink } from "@/components/auth/authFormClasses";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { usePageTitle } from "@/hooks/usePageTitle";
import { clearPendingRegistration, readPendingRegistration } from "@/lib/pendingRegistration";
import { mapRegistrationError } from "@/lib/registrationErrors";
import { validateCode, type AccountType } from "@/lib/registrationValidation";

function getStateEmail(state: unknown) {
  if (typeof state !== "object" || state === null) return undefined;
  const { email } = state as Record<string, unknown>;
  return typeof email === "string" && email ? email : undefined;
}

// Reached after Create Account, and from Sign In (KR-74) with only an email for unverified users
export default function VerifyEmailPage() {
  const location = useLocation();
  const [saved] = useState(readPendingRegistration);
  const [verified, setVerified] = useState(false);
  usePageTitle(verified ? "Account Ready | KerjaReady" : "Verify Email | KerjaReady");

  const email = getStateEmail(location.state) ?? saved?.email;
  // The saved account type only applies when it was saved for this email
  const accountType = saved && saved.email === email ? saved.accountType : undefined;

  if (!email) return <Navigate to="/register" replace />;

  return (
    <AuthLayout>
      {verified ? (
        <AccountReady />
      ) : (
        <VerifyForm email={email} accountType={accountType} onVerified={() => setVerified(true)} />
      )}
    </AuthLayout>
  );
}

type VerifyFormProps = {
  email: string;
  accountType?: AccountType;
  onVerified: () => void;
};

function VerifyForm({ email, accountType, onVerified }: VerifyFormProps) {
  const [code, setCode] = useState("");
  const [codeError, setCodeError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const codeRef = useRef<HTMLInputElement>(null);
  const formAlertRef = useRef<HTMLDivElement>(null);

  function showError(error: unknown) {
    const mapped = mapRegistrationError(error);
    const isCodeError = mapped.field === "code";
    flushSync(() => {
      setPending(false);
      setCodeError(isCodeError ? mapped.message : null);
      setFormError(isCodeError ? null : mapped.message);
    });
    (isCodeError ? codeRef.current : formAlertRef.current)?.focus();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    const error = validateCode(code);
    flushSync(() => {
      setCodeError(error);
      setFormError(null);
    });
    if (error) {
      codeRef.current?.focus();
      return;
    }

    setPending(true);
    try {
      await confirmSignUp({ username: email, confirmationCode: code.trim() });
      clearPendingRegistration();
      onVerified();
    } catch (caught) {
      showError(caught);
    }
  }

  return (
    <>
      <div aria-hidden="true" className={iconTile}>
        <Mail />
      </div>

      <h1 className="mt-6 text-2xl font-semibold">Check Your Email</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        We sent a 6-digit code to{" "}
        <span className="font-medium break-words text-foreground">{email}</span>. Enter it below to
        verify your email.
      </p>

      <form noValidate onSubmit={handleSubmit} className="mt-8 space-y-6">
        <div className="space-y-2">
          <Label htmlFor="code">Verification Code</Label>
          <CodeInput
            ref={codeRef}
            id="code"
            name="code"
            value={code}
            onValueChange={(value) => {
              setCode(value);
              setCodeError(null);
            }}
            aria-invalid={codeError ? true : undefined}
            aria-describedby={codeError ? "code-error" : undefined}
          />
          {codeError && <FieldError id="code-error">{codeError}</FieldError>}
        </div>

        {formError && <FormAlert ref={formAlertRef} message={formError} />}

        <SubmitButton pending={pending} pendingLabel="Verifying email…">
          Verify Email
        </SubmitButton>
      </form>

      <ResendCode
        onResend={async () => {
          await resendSignUpCode({ username: email });
        }}
        onStart={() => setFormError(null)}
        onSent={() => setCodeError(null)}
        onError={showError}
        hint="Check your spam folder. The code expires in 24 hours."
      />

      <div className="mt-6 border-t border-border pt-4 text-center">
        <Link
          to={accountType ? `/register/${accountType}` : "/register"}
          className={`underline underline-offset-2 ${quietLink}`}
        >
          Use a Different Email
        </Link>
      </div>
    </>
  );
}

function AccountReady() {
  const headingRef = useRef<HTMLHeadingElement>(null);

  // The form is replaced in place, so move focus to the new heading
  useEffect(() => headingRef.current?.focus(), []);

  return (
    <div className="text-center">
      <div aria-hidden="true" className={`mx-auto ${iconTile}`}>
        <Check />
      </div>
      <h1 ref={headingRef} tabIndex={-1} className="mt-6 text-2xl font-semibold outline-none">
        Your Account Is Ready
      </h1>
      <p className="mt-2 text-base leading-relaxed text-pretty text-muted-foreground">
        Your email is verified. Sign in to start using KerjaReady.
      </p>
      <Button asChild className="mt-8 w-full">
        <Link to="/sign-in">Sign In</Link>
      </Button>
    </div>
  );
}
