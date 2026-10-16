import type { Ref } from "react";
import { Target } from "lucide-react";
import FormAlert from "@/components/auth/FormAlert";
import LoadingButton from "@/components/LoadingButton";
import { Button } from "@/components/ui/button";
import type { Role } from "@/lib/candidateProfileApi";
import { profileCard, sectionIconTile } from "./styles";

type TargetRoleCardProps = {
  targetRole: Role | null;
  clearing: boolean;
  clearError: string | null;
  onChoose: () => void;
  onClear: () => void;
  // Attached to Choose Target Role or Change Target Role, whichever is showing
  actionRef: Ref<HTMLButtonElement>;
};

function TargetIcon() {
  return (
    <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
      <Target aria-hidden="true" />
    </div>
  );
}

// The saved target role with Change and Clear, or the empty state with Choose Target Role
export default function TargetRoleCard({
  targetRole,
  clearing,
  clearError,
  onChoose,
  onClear,
  actionRef,
}: TargetRoleCardProps) {
  return (
    <section aria-labelledby="target-role-heading" className={profileCard}>
      <h2 id="target-role-heading" className="text-xl font-semibold">
        Target Role
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Skill gap analysis and your learning roadmap are based on this role.
      </p>

      <div className="mt-5 border-t pt-6">
        {targetRole ? (
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex min-w-0 items-center gap-4">
              <TargetIcon />
              <div className="min-w-0">
                <p className="text-sm text-muted-foreground">Current target role</p>
                <p className="text-lg font-semibold break-words">{targetRole.title}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button ref={actionRef} variant="outline" disabled={clearing} onClick={onChoose}>
                Change Target Role
              </Button>
              <LoadingButton variant="ghost" pending={clearing} pendingLabel="Clearing…" onClick={onClear}>
                Clear Target Role
              </LoadingButton>
            </div>
          </div>
        ) : (
          <div className="flex items-start gap-4">
            <TargetIcon />
            <div className="min-w-0">
              <h3 className="text-base font-semibold">No Target Role Yet</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Choose the role you are aiming for. You can change or clear it at any time.
              </p>
              <Button ref={actionRef} className="mt-4" onClick={onChoose}>
                Choose Target Role
              </Button>
            </div>
          </div>
        )}

        {clearError && (
          <div className="mt-4">
            <FormAlert message={clearError} />
          </div>
        )}
      </div>
    </section>
  );
}
