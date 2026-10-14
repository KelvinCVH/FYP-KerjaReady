import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { Hub } from "aws-amplify/utils";
import { LoaderCircle } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import { usePageTitle } from "@/hooks/usePageTitle";
import { cleanCognitoMessage } from "@/lib/cognitoMessages";
import { hasSession, redirectSignedInUser } from "@/lib/userRole";

const GOOGLE_FAILED_MESSAGE = "Google sign-in didn’t finish. Try again.";
const TIMEOUT_MS = 15_000;

// Cognito returns here after Google. Amplify's OAuth listener exchanges the code for tokens.
export default function AuthCallbackPage() {
  usePageTitle("Signing In | KerjaReady");

  const navigate = useNavigate();
  // Set once the page has decided where to go, so StrictMode's second effect run does nothing
  const handled = useRef(false);

  useEffect(() => {
    let active = true;

    function goToSignIn(error?: string) {
      if (handled.current) return;
      handled.current = true;
      navigate("/sign-in", { replace: true, state: error ? { error } : null });
    }

    async function finishSignIn() {
      if (handled.current) return;
      handled.current = true;
      // With no role the user is signed out, so Sign In shows the saved error
      if (!(await redirectSignedInUser(navigate))) navigate("/sign-in", { replace: true });
    }

    const params = new URLSearchParams(window.location.search);
    const errorDescription = params.get("error_description");
    // The pre sign-up Lambda rejected the Google account, for example a recruiter email
    if (errorDescription) {
      goToSignIn(cleanCognitoMessage(errorDescription));
      return;
    }
    if (params.get("error")) {
      goToSignIn(GOOGLE_FAILED_MESSAGE);
      return;
    }
    if (!params.get("code")) {
      goToSignIn();
      return;
    }

    const stopListening = Hub.listen("auth", ({ payload }) => {
      if (payload.event === "signInWithRedirect") void finishSignIn();
      if (payload.event === "signInWithRedirect_failure") goToSignIn(GOOGLE_FAILED_MESSAGE);
    });

    // The listener can finish before this page mounts. fetchAuthSession waits for it, so check once.
    hasSession().then((signedIn) => {
      if (active && signedIn) void finishSignIn();
    });

    const timer = window.setTimeout(() => goToSignIn(GOOGLE_FAILED_MESSAGE), TIMEOUT_MS);

    return () => {
      active = false;
      stopListening();
      window.clearTimeout(timer);
    };
  }, [navigate]);

  return (
    <AuthLayout>
      <div role="status" className="flex flex-col items-center gap-4 py-10 text-center">
        <LoaderCircle aria-hidden="true" className="size-6 animate-spin text-primary" />
        <h1 className="text-2xl font-semibold">Signing you in…</h1>
      </div>
    </AuthLayout>
  );
}
