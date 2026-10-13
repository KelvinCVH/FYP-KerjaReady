import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import PlaceholderPage from "../../components/PlaceholderPage";

export default function RegisterPage() {
  return (
    <main className="flex min-h-[100dvh] items-center justify-center bg-background p-6">
      <PlaceholderPage
        title="Create Account"
        description="Create a candidate or recruiter account, then verify your email."
      >
        <Button asChild variant="outline">
          <Link to="/sign-in">Back to Sign In</Link>
        </Button>
      </PlaceholderPage>
    </main>
  );
}
