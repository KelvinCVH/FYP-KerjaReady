import { useRef, useState, type FormEvent } from "react";
import { flushSync } from "react-dom";
import { Link, useNavigate } from "react-router";
import { resetPassword } from "aws-amplify/auth";
import { ArrowLeft, Info } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import FormAlert from "@/components/auth/FormAlert";
import FormField from "@/components/auth/FormField";
import SubmitButton from "@/components/auth/SubmitButton";
import { quietLink } from "@/components/auth/authFormClasses";
import { Input } from "@/components/ui/input";
import { usePageTitle } from "@/hooks/usePageTitle";
import { savePendingPasswordReset } from "@/lib/pendingPasswordReset";
import { normaliseEmail, validateEmail } from "@/lib/registrationValidation";
import { mapSignInError } from "@/lib/signInErrors";

export default function ForgotPasswordPage() {
  usePageTitle("Forgot Password | KerjaReady");

  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const emailRef = useRef<HTMLInputElement>(null);
  const formAlertRef = useRef<HTMLDivElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    const error = validateEmail(email);
    flushSync(() => {
      setEmailError(error);
      setFormError(null);
    });
    if (error) {
      emailRef.current?.focus();
      return;
    }

    const username = normaliseEmail(email);
    setPending(true);
    try {
      // Cognito answers the same way for unknown emails, so this never reveals whether an account exists
      await resetPassword({ username });
      savePendingPasswordReset(username);
      navigate("/reset-password", { state: { email: username } });
    } catch (caught) {
      flushSync(() => {
        setPending(false);
        setFormError(mapSignInError(caught).message);
      });
      formAlertRef.current?.focus();
    }
  }

  return (
    <AuthLayout>
      <Link to="/sign-in" className={`inline-flex items-center gap-2 ${quietLink}`}>
        <ArrowLeft aria-hidden="true" className="size-4" />
        Back to Sign In
      </Link>

      <h1 className="mt-4 text-2xl font-semibold text-balance">Reset Your Password</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        Enter the email for your KerjaReady account and we’ll send you a 6-digit reset code.
      </p>

      <form noValidate onSubmit={handleSubmit} className="mt-8 space-y-6">
        <FormField id="email" label="Email" error={emailError}>
          {(aria) => (
            <Input
              {...aria}
              ref={emailRef}
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              spellCheck={false}
              autoCapitalize="none"
              placeholder="nurul.aina@example.com…"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                setEmailError(null);
              }}
            />
          )}
        </FormField>

        {formError && <FormAlert ref={formAlertRef} message={formError} />}

        <SubmitButton pending={pending} pendingLabel="Sending code…">
          Send Reset Code
        </SubmitButton>
      </form>

      <div className="mt-6 flex gap-3 rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
        <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
        <p>
          Created your account with Google? It has no KerjaReady password. Go back and choose
          Continue with Google instead.
        </p>
      </div>
    </AuthLayout>
  );
}
