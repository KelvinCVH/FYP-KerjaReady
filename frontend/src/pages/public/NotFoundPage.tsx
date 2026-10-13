import { Link } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";
import { usePageTitle } from "@/hooks/usePageTitle";

export default function NotFoundPage() {
  usePageTitle("Page Not Found | KerjaReady");

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
      <PlaceholderPage title="Page not found" description="The page you are looking for does not exist.">
        <Link to="/" className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100">
          Go to home
        </Link>
      </PlaceholderPage>
    </main>
  );
}