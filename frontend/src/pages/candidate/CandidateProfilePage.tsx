import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { CircleCheck } from "lucide-react";
import AccountDetailsCard from "@/components/profile/AccountDetailsCard";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import ProfileSkeleton from "@/components/profile/ProfileSkeleton";
import RolePickerDialog from "@/components/profile/RolePickerDialog";
import TargetRoleCard from "@/components/profile/TargetRoleCard";
import { useApiData } from "@/hooks/useApiData";
import { usePageTitle } from "@/hooks/usePageTitle";
import { getApiErrorMessage } from "@/lib/apiClient";
import { getCandidateProfile, getRoles, saveTargetRole, type Role } from "@/lib/profileApi";

// The profile and the role list load together; the page waits for both
async function loadProfileAndRoles() {
  const [profile, roles] = await Promise.all([getCandidateProfile(), getRoles()]);
  return { profile, roles };
}

export default function CandidateProfilePage() {
  usePageTitle("Profile | KerjaReady");

  const { state: page, retry, setData } = useApiData(loadProfileAndRoles);
  // Success message under the header, cleared by the next action
  const [notice, setNotice] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerKey, setPickerKey] = useState(0);
  const [clearing, setClearing] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);
  // Choose Target Role or Change Target Role, whichever is showing
  const roleActionRef = useRef<HTMLButtonElement>(null);

  function setTargetRole(targetRole: Role | null) {
    setData((data) => ({ ...data, profile: { ...data.profile, target_role: targetRole } }));
  }

  function openPicker() {
    setNotice(null);
    setClearError(null);
    setPickerKey((key) => key + 1);
    setPickerOpen(true);
  }

  function handleSaved(role: Role | null) {
    setTargetRole(role);
    setNotice("Target role saved.");
    setPickerOpen(false);
  }

  // After a save from the empty state the opening button is gone, so focus the one that replaced it
  function focusRoleAction(event: Event) {
    event.preventDefault();
    roleActionRef.current?.focus();
  }

  async function clearTargetRole() {
    setNotice(null);
    setClearError(null);
    setClearing(true);
    try {
      const role = await saveTargetRole(null);
      // Render the empty state now, so Choose Target Role exists to take focus from the removed Clear button
      flushSync(() => {
        setTargetRole(role);
        setNotice("Target role cleared.");
        setClearing(false);
      });
      roleActionRef.current?.focus();
    } catch (error) {
      setClearError(getApiErrorMessage(error));
      setClearing(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-semibold">Profile</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        Your account details and the role you are aiming for.
      </p>

      {/* Always in the page, so screen readers announce a message when it appears */}
      <div role="status">
        {notice && (
          <p className="mt-6 flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            <CircleCheck aria-hidden="true" className="size-4 shrink-0" />
            {notice}
          </p>
        )}
      </div>

      <div className="mt-6">
        {page.status === "loading" && <ProfileSkeleton accountType="candidate" />}
        {page.status === "error" && (
          <ProfileLoadError status={page.httpStatus} message={page.message} onRetry={retry} />
        )}
        {page.status === "ready" && (
          <div className="space-y-6">
            <TargetRoleCard
              targetRole={page.data.profile.target_role}
              clearing={clearing}
              clearError={clearError}
              onChoose={openPicker}
              onClear={clearTargetRole}
              actionRef={roleActionRef}
            />
            <AccountDetailsCard profile={page.data.profile} />
          </div>
        )}
      </div>

      {page.status === "ready" && (
        <RolePickerDialog
          key={pickerKey}
          open={pickerOpen}
          onOpenChange={setPickerOpen}
          roles={page.data.roles}
          savedRole={page.data.profile.target_role}
          onSaved={handleSaved}
          onCloseAutoFocus={focusRoleAction}
        />
      )}
    </div>
  );
}
