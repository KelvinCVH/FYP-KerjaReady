import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router";
import {
  DASHBOARD_PATHS,
  getUserRole,
  hasSession,
  signOutWithoutRole,
  type UserRole,
} from "@/lib/userRole";

type RequireRoleProps = {
  role: UserRole;
  children: ReactNode;
};

type Status = { allowed: true } | { allowed: false; redirectTo: string } | null;

// Lets only users with this role into a route tree. Signed-out users (including expired sessions) go to
// Sign In, users with the other role go to their own dashboard, and users with no role are signed out.
export default function RequireRole({ role, children }: RequireRoleProps) {
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      const userRole = await getUserRole();
      let next: Status;
      if (userRole === role) {
        next = { allowed: true };
      } else if (userRole) {
        next = { allowed: false, redirectTo: DASHBOARD_PATHS[userRole] };
      } else {
        // Sign In shows the saved no-role error
        if (await hasSession()) await signOutWithoutRole();
        next = { allowed: false, redirectTo: "/sign-in" };
      }
      if (active) setStatus(next);
    })();
    return () => {
      active = false;
    };
  }, [role]);

  if (!status) return null;
  if (!status.allowed) return <Navigate to={status.redirectTo} replace />;
  return children;
}
