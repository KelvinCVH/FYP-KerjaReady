import { useEffect, useRef, useState, type FormEvent } from "react";
import { flushSync } from "react-dom";
import { Link, useLocation, useNavigate } from "react-router";
import { resendSignUpCode, signIn } from "aws-amplify/auth";
import AuthLayout from "@/components/auth/AuthLayout";
import FormAlert from "@/components/auth/FormAlert";
import FormField from "@/components/auth/FormField";
import GoogleSignInButton from "@/components/auth/GoogleSignInButton";
import OrDivider from "@/components/auth/OrDivider";
import PasswordInput from "@/components/auth/PasswordInput";
import SubmitButton from "@/components/auth/SubmitButton";
import { accentLink, inlineLink } from "@/components/auth/authFormClasses";
import { Input } from "@/components/ui/input";
import { usePageTitle } from "@/hooks/usePageTitle";
import { GENERIC_ERROR_MESSAGE, getErrorName } from "@/lib/cognitoMessages";
import { savePendingRegistration } from "@/lib/pendingRegistration";
import { normaliseEmail, validateEmail } from "@/lib/registrationValidation";
import { mapSignInError } from "@/lib/signInErrors";
import { clearSignInError, readSignInError } from "@/lib/signInNotice";
import { hasSession, NO_ROLE_MESSAGE, redirectSignedInUser } from "@/lib/userRole";

const PASSWORD_RESET_NOTICE = "Your password has been reset. Sign in with your new password.";

type FieldName = "email" | "password";
type FieldErrors = Partial<Record<FieldName, string>>;

// Router state set by the Google callback ({ error }) and by Reset Password ({ notice, email })
type SignInState = { error?: string; notice?: "password-reset"; email?: string };

function readSignInState(state: unknown): SignInState {
  if (typeof state !== "object" || state === null) return {};
  const { error, notice, email } = state as Record<string, unknown>;
  return {
    error: typeof error === "string" && error ? error : undefined,
    notice: notice === "password-reset" ? notice : undefined,
    email: typeof email === "string" ? email : undefined,
  };
}

export default function SignInPage() {
  usePageTitle("Sign In | KerjaReady");

  const navigate = useNavigate();
  const location = useLocation();
  const [initial] = useState(() => readSignInState(location.state));

  const [email, setEmail] = useState(initial.notice ? (initial.email ?? "") : "");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  // The no-role error is saved in storage because Google sign-out reloads the page
  const [formError, setFormError] = useState<string | null>(
    () => initial.error ?? readSignInError(),
  );
  const [notice, setNotice] = useState(initial.notice ? PASSWORD_RESET_NOTICE : null);
  const [pending, setPending] = useState(false);

  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const formAlertRef = useRef<HTMLDivElement>(null);

  const fieldRefs: Record<FieldName, { current: HTMLElement | null }> = {
    email: emailRef,
    password: passwordRef,
  };

  useEffect(() => {
    clearSignInError();
    // Drop the router state so a refresh does not show the message again
    if (location.state) navigate(".", { replace: true, state: null });
    // After a password reset the email is filled in, so continue at the password
    if (initial.notice) passwordRef.current?.focus();
    // Runs once for the state this page opened with
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function showFormError(message: string) {
    flushSync(() => {
      setPending(false);
      setNotice(null);
      setFormError(message);
    });
    formAlertRef.current?.focus();
  }

  // Already signed in (for example after Back from a dashboard): go straight to the dashboard
  useEffect(() => {
    let active = true;
    (async () => {
      if (!(await hasSession()) || !active) return;
      if (!(await redirectSignedInUser(navigate)) && active) {
        clearSignInError();
        setFormError(NO_ROLE_MESSAGE);
      }
    })();
    return () => {
      active = false;
    };
  }, [navigate]);

  async function goToDashboard() {
    if (await redirectSignedInUser(navigate)) return;
    clearSignInError();
    showFormError(NO_ROLE_MESSAGE);
  }

  function clearError(field: FieldName) {
    setErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    const nextErrors: FieldErrors = {};
    const emailError = validateEmail(email);
    if (emailError) nextErrors.email = emailError;
    if (!password) nextErrors.password = "Enter your password.";
    const firstInvalid = (["email", "password"] as const).find((field) => nextErrors[field]);
    flushSync(() => {
      setErrors(nextErrors);
      setFormError(null);
    });
    if (firstInvalid) {
      fieldRefs[firstInvalid].current?.focus();
      return;
    }

    const username = normaliseEmail(email);
    setPending(true);
    try {
      const { isSignedIn, nextStep } = await signIn({ username, password });
      if (isSignedIn) {
        await goToDashboard();
        return;
      }
      if (nextStep.signInStep === "CONFIRM_SIGN_UP") {
        // The account exists but the email is not verified yet: send a fresh code and verify it
        try {
          await resendSignUpCode({ username });
        } catch {
          // Verify Email has its own Resend Code, so continue
        }
        savePendingRegistration({ email: username });
        navigate("/register/verify", { state: { email: username } });
        return;
      }
      showFormError(GENERIC_ERROR_MESSAGE);
    } catch (caught) {
      if (getErrorName(caught) === "UserAlreadyAuthenticatedException") {
        await goToDashboard();
        return;
      }
      showFormError(mapSignInError(caught).message);
    }
  }

  return (
    <AuthLayout>
      <h1 className="text-2xl font-semibold text-balance">Sign In</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        Welcome back to KerjaReady.
      </p>

      {(formError || notice) && (
        <div className="mt-6">
          {formError ? (
            <FormAlert ref={formAlertRef} message={formError} />
          ) : (
            notice && <FormAlert variant="success" message={notice} />
          )}
        </div>
      )}

      <div className={`${formError || notice ? "mt-6" : "mt-8"} space-y-6`}>
        <form noValidate onSubmit={handleSubmit} className="space-y-6">
          <FormField id="email" label="Email" error={errors.email}>
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
                  clearError("email");
                }}
              />
            )}
          </FormField>

          <FormField
            id="password"
            label="Password"
            error={errors.password}
            labelAside={
              <Link to="/forgot-password" className={accentLink}>
                Forgot Password?
              </Link>
            }
          >
            {(aria) => (
              <PasswordInput
                {...aria}
                ref={passwordRef}
                id="password"
                name="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  clearError("password");
                }}
              />
            )}
          </FormField>

          <SubmitButton pending={pending} pendingLabel="Signing in…">
            Sign In
          </SubmitButton>
        </form>

        <OrDivider />

        <GoogleSignInButton />
      </div>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Don’t have an account?{" "}
        <Link to="/register" className={`font-medium ${inlineLink}`}>
          Create Account
        </Link>
      </p>
    </AuthLayout>
  );
}
