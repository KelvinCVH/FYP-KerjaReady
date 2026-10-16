import type { CandidateProfile } from "@/lib/candidateProfileApi";
import { profileCard } from "./styles";

const ACCOUNT_TYPE_LABELS: Record<CandidateProfile["account_type"], string> = {
  candidate: "Candidate",
};

// Read-only name, email and account type
export default function AccountDetailsCard({ profile }: { profile: CandidateProfile }) {
  // Names and email addresses are kept out of browser auto-translation
  const rows = [
    { label: "Full Name", value: profile.full_name, translate: "no" as const },
    { label: "Email", value: profile.email, translate: "no" as const },
    { label: "Account Type", value: ACCOUNT_TYPE_LABELS[profile.account_type] },
  ];

  return (
    <section aria-labelledby="account-details-heading" className={profileCard}>
      <h2 id="account-details-heading" className="text-xl font-semibold">
        Account Details
      </h2>
      <dl className="mt-1 divide-y">
        {rows.map(({ label, value, translate }) => (
          <div key={label} className="flex flex-col gap-1 py-3 md:flex-row md:items-baseline md:gap-0">
            <dt className="text-sm text-muted-foreground md:w-40 md:shrink-0">{label}</dt>
            <dd translate={translate} className="min-w-0 text-base leading-relaxed break-words">
              {value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
