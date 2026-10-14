import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { signInWithRedirect } from "aws-amplify/auth";
import { LoaderCircle } from "lucide-react";
import googleLogo from "@/assets/google-g-logo.png";
import FormAlert from "@/components/auth/FormAlert";
import { inlineLink } from "@/components/auth/authFormClasses";
import { GENERIC_ERROR_MESSAGE, getErrorName } from "@/lib/cognitoMessages";
import { redirectSignedInUser } from "@/lib/userRole";

// Google's light theme sign-in button spec: white fill, #747775 1px stroke, #1F1F1F text,
// 12px between logo and label, hover is Google's #303030 state layer at 8% (#EEEEEE on white).
// The official "G" logo is used unchanged at 18px.
const googleButton =
  "flex h-11 w-full items-center justify-center gap-3 rounded-lg border border-[#747775] bg-white px-3 text-sm font-medium text-[#1F1F1F] transition-[background-color,transform] duration-150 outline-none hover:bg-[#EEEEEE] focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50";

export default function GoogleSignInButton() {
  const navigate = useNavigate();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Coming Back from Google can restore this page from the back/forward cache with the spinner showing
  useEffect(() => {
    function handlePageShow(event: PageTransitionEvent) {
      if (event.persisted) setPending(false);
    }
    window.addEventListener("pageshow", handlePageShow);
    return () => window.removeEventListener("pageshow", handlePageShow);
  }, []);

  async function handleClick() {
    if (pending) return;

    setPending(true);
    setError(null);
    try {
      // Leaves the page for Google. Cognito returns to /auth/callback.
      await signInWithRedirect({ provider: "Google" });
    } catch (caught) {
      if (getErrorName(caught) === "UserAlreadyAuthenticatedException") {
        // Reload Sign In if the session has no role, so it shows the saved error
        if (!(await redirectSignedInUser(navigate))) window.location.replace("/sign-in");
        return;
      }
      setPending(false);
      setError(GENERIC_ERROR_MESSAGE);
    }
  }

  return (
    <div className="space-y-3">
      <span role="status" className="sr-only">
        {pending ? "Redirecting to Google…" : ""}
      </span>
      <button type="button" onClick={handleClick} disabled={pending} className={googleButton}>
        {pending ? (
          <LoaderCircle aria-hidden="true" className="size-[18px] animate-spin" />
        ) : (
          <img src={googleLogo} alt="" width={18} height={18} className="size-[18px]" />
        )}
        Continue with Google
      </button>

      {error && <FormAlert message={error} />}

      <p className="text-center text-sm text-pretty text-muted-foreground">
        By continuing with Google, you agree to the{" "}
        <Link to="/privacy" target="_blank" rel="noopener" className={inlineLink}>
          Privacy Notice
          <span className="sr-only"> (opens in a new tab)</span>
        </Link>
        .
      </p>
    </div>
  );
}
