import AccountDetailsCard from "@/components/profile/AccountDetailsCard";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import ProfileSkeleton from "@/components/profile/ProfileSkeleton";
import { useApiData } from "@/hooks/useApiData";
import { usePageTitle } from "@/hooks/usePageTitle";
import { getRecruiterProfile } from "@/lib/profileApi";

// The recruiter's read-only account details, including their company. Recruiters have no target role.
export default function RecruiterProfilePage() {
  usePageTitle("Profile | KerjaReady");

  const { state: page, retry } = useApiData(getRecruiterProfile);

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-semibold">Profile</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">Your account and company details.</p>

      <div className="mt-6">
        {page.status === "loading" && <ProfileSkeleton accountType="recruiter" />}
        {page.status === "error" && (
          <ProfileLoadError status={page.httpStatus} message={page.message} onRetry={retry} />
        )}
        {page.status === "ready" && <AccountDetailsCard profile={page.data} />}
      </div>
    </div>
  );
}
