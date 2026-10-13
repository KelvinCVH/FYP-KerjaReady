import { Link } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";

const linkClass = "rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100";

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
      <PlaceholderPage title="Sign in" description="Sign in with your email and password.">
        {/* Temporary links until Cognito sign-in is built */}
        <Link to="/candidate/dashboard" className={linkClass}>Continue as candidate</Link>
        <Link to="/recruiter/dashboard" className={linkClass}>Continue as recruiter</Link>
        <Link to="/register" className={linkClass}>Create an account</Link>
      </PlaceholderPage>
    </main>
  );
}