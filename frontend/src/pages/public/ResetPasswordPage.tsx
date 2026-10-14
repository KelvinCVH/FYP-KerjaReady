import { useRef, useState, type FormEvent } from "react";
import { flushSync } from "react-dom";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { confirmResetPassword, resetPassword } from "aws-amplify/auth";
import { ArrowLeft } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import CodeInput from "@/components/auth/CodeInput";
import FormAlert from "@/components/auth/FormAlert";
import FormField from "@/components/auth/FormField";
import PasswordInput from "@/components/auth/PasswordInput";
import ResendCode from "@/components/auth/ResendCode";
import SubmitButton from "@/components/auth/SubmitButton";
import { quietLink } from "@/components/auth/authFormClasses";
import { usePageTitle } from "@/hooks/usePageTitle";
import { clearPendingPasswordReset, readPendingPasswordReset } from "@/lib/pendingPasswordReset";
import { PASSWORD_HINT, validateCode, validatePassword } from "@/lib/registrationValidation";
import { mapSignInError } from "@/lib/signInErrors";

type FieldName = "code" | "password";
type FieldErrors = Partial<Record<FieldName, string>>;

function getStateEmail(state: unknown) {
  if (typeof state !== "object" || state === null) return undefined;
  const { email } = state as Record<string, unknown>;
  return typeof email === "string" && email ? email : undefined;
}

export default function ResetPasswordPage() {
  usePageTitle("Reset Password | KerjaReady");

  const location = useLocation();
  const [saved] = useState(readPendingPasswordReset);
  const email = getStateEmail(location.state) ?? saved;

  if (!email) return <Navigate to="/forgot-password" replace />;

  return (
    <AuthLayout>
      <ResetPasswordForm email={email} />
    </AuthLayout>
  );
}

function ResetPasswordForm({ email }: { email: string }) {
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const codeRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const formAlertRef = useRef<HTMLDivElement>(null);

  const fieldRefs: Record<FieldName, { current: HTMLElement | null }> = {
    code: codeRef,
    password: passwordRef,
  };

  function clearError(field: FieldName) {
    setErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function showError(error: unknown) {
    const mapped = mapSignInError(error, { password });
    const field = mapped.field === "form" ? null : mapped.field;
    flushSync(() => {
      setPending(false);
      setErrors(field ? { [field]: mapped.message } : {});
      setFormError(field ? null : mapped.message);
    });
    (field ? fieldRefs[field].current : formAlertRef.current)?.focus();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    const nextErrors: FieldErrors = {};
    const codeError = validateCode(code);
    const passwordError = validatePassword(password);
    if (codeError) nextErrors.code = codeError;
    if (passwordError) nextErrors.password = passwordError;
    const firstInvalid = (["code", "password"] as const).find((field) => nextErrors[field]);
    flushSync(() => {
      setErrors(nextErrors);
      setFormError(null);
    });
    if (firstInvalid) {
      fieldRefs[firstInvalid].current?.focus();
      return;
    }

    setPending(true);
    try {
      await confirmResetPassword({
        username: email,
        confirmationCode: code.trim(),
        newPassword: password,
      });
      clearPendingPasswordReset();
      navigate("/sign-in", { replace: true, state: { notice: "password-reset", email } });
    } catch (caught) {
      showError(caught);
    }
  }

  return (
    <>
      <Link to="/forgot-password" className={`inline-flex items-center gap-2 ${quietLink}`}>
        <ArrowLeft aria-hidden="true" className="size-4" />
        Use a Different Email
      </Link>

      <h1 className="mt-4 text-2xl font-semibold text-balance">Set a New Password</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        We sent a 6-digit code to{" "}
        <span className="font-medium break-words text-foreground">{email}</span>. Enter it below
        with your new password.
      </p>

      <form noValidate onSubmit={handleSubmit} className="mt-8 space-y-6">
        {/* Lets password managers save the new password against this account */}
        <input type="email" name="username" autoComplete="username" value={email} readOnly hidden />

        <FormField id="code" label="Reset Code" error={errors.code}>
          {(aria) => (
            <CodeInput
              {...aria}
              ref={codeRef}
              id="code"
              name="code"
              value={code}
              onValueChange={(value) => {
                setCode(value);
                clearError("code");
              }}
            />
          )}
        </FormField>

        <FormField id="password" label="New Password" error={errors.password} helper={PASSWORD_HINT}>
          {(aria) => (
            <PasswordInput
              {...aria}
              ref={passwordRef}
              id="password"
              name="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                clearError("password");
              }}
            />
          )}
        </FormField>

        {formError && <FormAlert ref={formAlertRef} message={formError} />}

        <SubmitButton pending={pending} pendingLabel="Resetting password…">
          Reset Password
        </SubmitButton>
      </form>

      <ResendCode
        onResend={async () => {
          await resetPassword({ username: email });
        }}
        onStart={() => setFormError(null)}
        onSent={() => clearError("code")}
        onError={showError}
        hint="Check your spam folder. The code expires in 1 hour."
      />
    </>
  );
}
