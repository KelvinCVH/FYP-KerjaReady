import { Link } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
      <PlaceholderPage
        title="Create an account"
        description="Register as a candidate or recruiter, then verify your email."
      >
        <Link to="/sign-in" className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100">
          Back to sign in
        </Link>
      </PlaceholderPage>
    </main>
  );
}