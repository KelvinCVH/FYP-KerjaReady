import { cn } from "cn";
import type { CandidateProfile, RecruiterProfile } from "@/lib/profileApi";
import { profileCard } from "./styles";

type Profile = CandidateProfile | RecruiterProfile;

type Row = {
  label: string;
  value: string;
  // Names, email addresses and company names are kept out of browser auto-translation
  noTranslate?: boolean;
  // A placeholder rather than real data
  missing?: boolean;
};

const ACCOUNT_TYPE_LABELS: Record<Profile["account_type"], string> = {
  candidate: "Candidate",
  recruiter: "Recruiter",
};

// Read-only name, email, company (recruiters only) and account type
export default function AccountDetailsCard({ profile }: { profile: Profile }) {
  const rows: Row[] = [
    { label: "Full Name", value: profile.full_name, noTranslate: true },
    { label: "Email", value: profile.email, noTranslate: true },
  ];
  if (profile.account_type === "recruiter") {
    rows.push(
      profile.company_name
        ? { label: "Company Name", value: profile.company_name, noTranslate: true }
        : { label: "Company Name", value: "Not provided", missing: true },
    );
  }
  rows.push({ label: "Account Type", value: ACCOUNT_TYPE_LABELS[profile.account_type] });

  return (
    <section aria-labelledby="account-details-heading" className={profileCard}>
      <h2 id="account-details-heading" className="text-xl font-semibold">
        Account Details
      </h2>
      <dl className="mt-1 divide-y">
        {rows.map(({ label, value, noTranslate, missing }) => (
          <div key={label} className="flex flex-col gap-1 py-3 md:flex-row md:items-baseline md:gap-0">
            <dt className="text-sm text-muted-foreground md:w-40 md:shrink-0">{label}</dt>
            <dd
              translate={noTranslate ? "no" : undefined}
              className={cn("min-w-0 text-base leading-relaxed break-words", missing && "text-muted-foreground")}
            >
              {value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
