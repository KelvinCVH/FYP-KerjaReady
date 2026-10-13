import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import PlaceholderPage from "../../components/PlaceholderPage";
import { usePageTitle } from "@/hooks/usePageTitle";

export default function SignInPage() {
  usePageTitle("Sign In | KerjaReady");

  return (
    <main className="flex min-h-[100dvh] items-center justify-center bg-background p-6">
      <PlaceholderPage title="Sign In" description="Sign in with your email and password.">
        {/* Temporary links until Cognito sign-in is built */}
        <Button asChild variant="outline">
          <Link to="/candidate/dashboard">Continue as Candidate</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/recruiter/dashboard">Continue as Recruiter</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/register">Create Account</Link>
        </Button>
      </PlaceholderPage>
    </main>
  );
}
