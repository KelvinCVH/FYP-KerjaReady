import { useRef, useState, type FormEvent, type ReactNode } from "react";
import { flushSync } from "react-dom";
import { Link, useNavigate } from "react-router";
import { signUp } from "aws-amplify/auth";
import { ArrowLeft } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import FieldError from "@/components/auth/FieldError";
import FormAlert from "@/components/auth/FormAlert";
import PasswordInput from "@/components/auth/PasswordInput";
import SignInPrompt from "@/components/auth/SignInPrompt";
import SubmitButton from "@/components/auth/SubmitButton";
import { errorLink, inlineLink, quietLink } from "@/components/auth/authFormClasses";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { savePendingRegistration } from "@/lib/pendingRegistration";
import { mapRegistrationError } from "@/lib/registrationErrors";
import {
  normaliseEmail,
  PASSWORD_HINT,
  validateCompanyName,
  validateEmail,
  validateFullName,
  validatePassword,
  type AccountType,
} from "@/lib/registrationValidation";
import { usePageTitle } from "@/hooks/usePageTitle";

type FieldName = "fullName" | "email" | "companyName" | "password" | "consent";
type FieldErrors = Partial<Record<FieldName, string>>;

const CONSENT_ERROR = "You must agree to the Privacy Notice to create an account.";

const pageCopy: Record<
  AccountType,
  { title: string; description: string; namePlaceholder: string; emailPlaceholder: string }
> = {
  candidate: {
    title: "Create a Candidate Account",
    description: "Your resume and results stay private until you apply for a job.",
    namePlaceholder: "Nurul Aina binti Razak…",
    emailPlaceholder: "nurul.aina@example.com…",
  },
  recruiter: {
    title: "Create a Recruiter Account",
    description: "Post roles and review applicants who apply to your listings.",
    namePlaceholder: "Daniel Lim Wei Jie…",
    emailPlaceholder: "daniel.lim@example.com…",
  },
};

type FieldProps = {
  id: string;
  label: string;
  error?: ReactNode;
  helper?: string;
  // Receives the aria props to spread on the control
  children: (aria: { "aria-invalid"?: true; "aria-describedby"?: string }) => ReactNode;
};

// Label above the control, then the error, then the helper text (DESIGN.md 9.2)
function Field({ id, label, error, helper, children }: FieldProps) {
  const errorId = `${id}-error`;
  const helperId = `${id}-helper`;
  const describedBy = [error && errorId, helper && helperId].filter(Boolean).join(" ");

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
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

type AccountDetailsPageProps = {
  accountType: AccountType;
};

export default function AccountDetailsPage({ accountType }: AccountDetailsPageProps) {
  usePageTitle("Create Account | KerjaReady");

  const navigate = useNavigate();
  const copy = pageCopy[accountType];
  const isRecruiter = accountType === "recruiter";

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [password, setPassword] = useState("");
  const [consent, setConsent] = useState(false);

  const [errors, setErrors] = useState<FieldErrors>({});
  const [emailExists, setEmailExists] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const fullNameRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const companyNameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const consentRef = useRef<HTMLButtonElement>(null);
  const formAlertRef = useRef<HTMLDivElement>(null);

  const fieldRefs: Record<FieldName, { current: HTMLElement | null }> = {
    fullName: fullNameRef,
    email: emailRef,
    companyName: companyNameRef,
    password: passwordRef,
    consent: consentRef,
  };
  // Visual order, used to focus the first invalid field
  const fieldOrder: FieldName[] = isRecruiter
    ? ["fullName", "email", "companyName", "password", "consent"]
    : ["fullName", "email", "password", "consent"];

  function clearError(field: FieldName) {
    if (field === "email") setEmailExists(false);
    setErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function validate(): FieldErrors {
    const result: FieldErrors = {
      fullName: validateFullName(fullName) ?? undefined,
      email: validateEmail(email) ?? undefined,
      companyName: isRecruiter ? (validateCompanyName(companyName) ?? undefined) : undefined,
      password: validatePassword(password) ?? undefined,
      consent: consent ? undefined : CONSENT_ERROR,
    };
    return Object.fromEntries(
      Object.entries(result).filter(([, message]) => message),
    ) as FieldErrors;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    const nextErrors = validate();
    const firstInvalid = fieldOrder.find((field) => nextErrors[field]);
    flushSync(() => {
      setErrors(nextErrors);
      setEmailExists(false);
      setFormError(null);
    });
    if (firstInvalid) {
      fieldRefs[firstInvalid].current?.focus();
      return;
    }

    const normalisedEmail = normaliseEmail(email);
    setPending(true);
    try {
      await signUp({
        username: normalisedEmail,
        password,
        options: {
          userAttributes: {
            email: normalisedEmail,
            name: fullName.trim(),
            "custom:account_type": accountType,
            // The pre sign-up Lambda rejects a company name on candidate accounts
            ...(isRecruiter && { "custom:company_name": companyName.trim() }),
          },
          validationData: { privacy_consent: "true" },
        },
      });
      savePendingRegistration({ email: normalisedEmail, accountType });
      navigate("/register/verify", { state: { email: normalisedEmail } });
    } catch (error) {
      const mapped = mapRegistrationError(error, { password });
      const field = mapped.field === "email" || mapped.field === "password" ? mapped.field : null;
      flushSync(() => {
        setPending(false);
        if (field) {
          setErrors({ [field]: mapped.message });
          setEmailExists(Boolean(mapped.signInLink));
        } else {
          setFormError(mapped.message);
        }
      });
      (field ? fieldRefs[field].current : formAlertRef.current)?.focus();
    }
  }

  return (
    <AuthLayout>
      <Link to={`/register?role=${accountType}`} className={`inline-flex items-center gap-2 ${quietLink}`}>
        <ArrowLeft aria-hidden="true" className="size-4" />
        Change Account Type
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">{copy.title}</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">{copy.description}</p>

      <form noValidate onSubmit={handleSubmit} className="mt-8 space-y-6">
        <Field id="full-name" label="Full Name" error={errors.fullName}>
          {(aria) => (
            <Input
              {...aria}
              ref={fullNameRef}
              id="full-name"
              name="name"
              autoComplete="name"
              placeholder={copy.namePlaceholder}
              value={fullName}
              onChange={(event) => {
                setFullName(event.target.value);
                clearError("fullName");
              }}
            />
          )}
        </Field>

        <Field
          id="email"
          label="Email"
          error={
            errors.email &&
            (emailExists ? (
              <>
                {errors.email}{" "}
                <Link to="/sign-in" className={errorLink}>
                  Sign In
                </Link>{" "}
                instead.
              </>
            ) : (
              errors.email
            ))
          }
        >
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
              placeholder={copy.emailPlaceholder}
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                clearError("email");
              }}
            />
          )}
        </Field>

        {isRecruiter && (
          <Field
            id="company-name"
            label="Company Name"
            error={errors.companyName}
            helper="Candidates see your company name on your listings."
          >
            {(aria) => (
              <Input
                {...aria}
                ref={companyNameRef}
                id="company-name"
                name="organization"
                autoComplete="organization"
                placeholder="Example Technologies Sdn Bhd…"
                value={companyName}
                onChange={(event) => {
                  setCompanyName(event.target.value);
                  clearError("companyName");
                }}
              />
            )}
          </Field>
        )}

        <Field id="password" label="Password" error={errors.password} helper={PASSWORD_HINT}>
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
        </Field>

        <div className="space-y-2">
          <div className="flex items-start gap-3">
            <Checkbox
              ref={consentRef}
              id="consent"
              name="privacy_consent"
              checked={consent}
              onCheckedChange={(checked) => {
                setConsent(checked === true);
                clearError("consent");
              }}
              aria-invalid={errors.consent ? true : undefined}
              aria-describedby={errors.consent ? "consent-error" : undefined}
              className="mt-0.5"
            />
            <label htmlFor="consent" className="text-sm leading-relaxed text-muted-foreground">
              I have read the{" "}
              <Link to="/privacy" target="_blank" rel="noopener" className={inlineLink}>
                Privacy Notice
                <span className="sr-only"> (opens in a new tab)</span>
              </Link>{" "}
              and agree to KerjaReady using my data as it describes.
            </label>
          </div>
          {errors.consent && <FieldError id="consent-error">{errors.consent}</FieldError>}
        </div>

        {formError && <FormAlert ref={formAlertRef} message={formError} />}

        <SubmitButton pending={pending} pendingLabel="Creating account…">
          Create Account
        </SubmitButton>
      </form>

      <SignInPrompt />
    </AuthLayout>
  );
}
