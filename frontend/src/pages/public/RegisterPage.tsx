import { useState } from "react";
import { Link, useSearchParams } from "react-router";
import { BriefcaseBusiness, GraduationCap, type LucideIcon } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import SignInPrompt from "@/components/auth/SignInPrompt";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import type { AccountType } from "@/lib/registrationValidation";
import { usePageTitle } from "@/hooks/usePageTitle";

type AccountOption = {
  value: AccountType;
  label: string;
  description: string;
  icon: LucideIcon;
};

const accountOptions: AccountOption[] = [
  {
    value: "candidate",
    label: "Candidate",
    description: "Assess your resume, see your skill gaps and apply for tech roles.",
    icon: GraduationCap,
  },
  {
    value: "recruiter",
    label: "Recruiter",
    description: "Post tech roles and review applicants with match scores.",
    icon: BriefcaseBusiness,
  },
];

function isAccountType(value: string | null): value is AccountType {
  return value === "candidate" || value === "recruiter";
}

export default function RegisterPage() {
  usePageTitle("Create Account | KerjaReady");

  // Landing page calls to action preselect a type with ?role=
  const [searchParams] = useSearchParams();
  const role = searchParams.get("role");
  const [accountType, setAccountType] = useState<AccountType>(
    isAccountType(role) ? role : "candidate",
  );
  const selected = accountOptions.find((option) => option.value === accountType)!;

  return (
    <AuthLayout>
      <h1 className="text-2xl font-semibold">Create Account</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        Choose the account that fits how you will use KerjaReady.
      </p>

      <RadioGroup
        aria-label="Account type"
        value={accountType}
        onValueChange={(value) => isAccountType(value) && setAccountType(value)}
        className="mt-8"
      >
        {accountOptions.map((option) => {
          const Icon = option.icon;
          const id = `account-type-${option.value}`;
          return (
            <label
              key={option.value}
              htmlFor={id}
              className="group flex cursor-pointer items-start gap-4 rounded-xl border border-input p-4 transition-[background-color,border-color] duration-150 not-has-[[data-state=checked]]:hover:bg-accent has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary-subtle has-[[data-state=checked]]:ring-1 has-[[data-state=checked]]:ring-primary has-focus-visible:ring-2 has-focus-visible:ring-ring has-focus-visible:ring-offset-2 has-focus-visible:ring-offset-card"
            >
              <span
                aria-hidden="true"
                className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted text-foreground group-has-[[data-state=checked]]:bg-card group-has-[[data-state=checked]]:text-primary"
              >
                <Icon className="size-5" />
              </span>
              <span className="min-w-0 flex-1">
                <span id={`${id}-label`} className="block text-base font-semibold">
                  {option.label}
                </span>
                <span
                  id={`${id}-description`}
                  className="mt-1 block text-sm text-muted-foreground"
                >
                  {option.description}
                </span>
              </span>
              <RadioGroupItem
                id={id}
                value={option.value}
                aria-labelledby={`${id}-label`}
                aria-describedby={`${id}-description`}
                className="mt-0.5 focus-visible:ring-0 focus-visible:ring-offset-0"
              />
            </label>
          );
        })}
      </RadioGroup>

      <Button asChild className="mt-8 w-full">
        <Link to={`/register/${accountType}`}>Continue as {selected.label}</Link>
      </Button>

      <SignInPrompt />
    </AuthLayout>
  );
}
