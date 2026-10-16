import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { CircleCheck } from "lucide-react";
import AccountDetailsCard from "@/components/profile/AccountDetailsCard";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import ProfileSkeleton from "@/components/profile/ProfileSkeleton";
import RolePickerDialog from "@/components/profile/RolePickerDialog";
import TargetRoleCard from "@/components/profile/TargetRoleCard";
import { usePageTitle } from "@/hooks/usePageTitle";
import { ApiError, getApiErrorMessage } from "@/lib/apiClient";
import {
  getCandidateProfile,
  getRoles,
  saveTargetRole,
  type CandidateProfile,
  type Role,
} from "@/lib/candidateProfileApi";

type PageState =
  | { status: "loading" }
  | { status: "error"; httpStatus: number; message: string }
  | { status: "ready"; profile: CandidateProfile; roles: Role[] };

export default function CandidateProfilePage() {
  usePageTitle("Profile | KerjaReady");

  const [page, setPage] = useState<PageState>({ status: "loading" });
  const [reloadKey, setReloadKey] = useState(0);
  // Success message under the header, cleared by the next action
  const [notice, setNotice] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerKey, setPickerKey] = useState(0);
  const [clearing, setClearing] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);
  // Choose Target Role or Change Target Role, whichever is showing
  const roleActionRef = useRef<HTMLButtonElement>(null);

  // The profile and the role list load together; the page waits for both
  useEffect(() => {
    let active = true;
    Promise.all([getCandidateProfile(), getRoles()]).then(
      ([profile, roles]) => {
        if (active) setPage({ status: "ready", profile, roles });
      },
      (error: unknown) => {
        if (!active) return;
        const httpStatus = error instanceof ApiError ? error.status : 0;
        setPage({ status: "error", httpStatus, message: getApiErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [reloadKey]);

  function retry() {
    setPage({ status: "loading" });
    setReloadKey((key) => key + 1);
  }

  function setTargetRole(targetRole: Role | null) {
    setPage((current) =>
      current.status === "ready" ? { ...current, profile: { ...current.profile, target_role: targetRole } } : current,
    );
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
        {page.status === "loading" && <ProfileSkeleton />}
        {page.status === "error" && (
          <ProfileLoadError status={page.httpStatus} message={page.message} onRetry={retry} />
        )}
        {page.status === "ready" && (
          <div className="space-y-6">
            <TargetRoleCard
              targetRole={page.profile.target_role}
              clearing={clearing}
              clearError={clearError}
              onChoose={openPicker}
              onClear={clearTargetRole}
              actionRef={roleActionRef}
            />
            <AccountDetailsCard profile={page.profile} />
          </div>
        )}
      </div>

      {page.status === "ready" && (
        <RolePickerDialog
          key={pickerKey}
          open={pickerOpen}
          onOpenChange={setPickerOpen}
          roles={page.roles}
          savedRole={page.profile.target_role}
          onSaved={handleSaved}
          onCloseAutoFocus={focusRoleAction}
        />
      )}
    </div>
  );
}
