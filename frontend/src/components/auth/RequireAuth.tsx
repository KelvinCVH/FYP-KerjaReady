import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router";
import { hasSession } from "@/lib/userRole";

type RequireAuthProps = {
  children: ReactNode;
};

// Sends signed-out users, including those whose session has expired, to Sign In.
// Checking that the role matches the route is KR-114.
export default function RequireAuth({ children }: RequireAuthProps) {
  const [status, setStatus] = useState<"checking" | "signed-in" | "signed-out">("checking");

  useEffect(() => {
    let active = true;
    hasSession().then((signedIn) => {
      if (active) setStatus(signedIn ? "signed-in" : "signed-out");
    });
    return () => {
      active = false;
    };
  }, []);

  if (status === "checking") return null;
  if (status === "signed-out") return <Navigate to="/sign-in" replace />;
  return children;
}
