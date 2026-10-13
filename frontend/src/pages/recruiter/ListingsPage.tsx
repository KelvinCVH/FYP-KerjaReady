import { Link } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";

const linkClass = "rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100";

export default function ListingsPage() {
  return (
    <PlaceholderPage title="Listings" description="Your job listings with the number of applicants.">
      <Link to="/recruiter/listings/new" className={linkClass}>Create listing</Link>
      {/* Sample links to test the routes; replaced by real listings later */}
      <Link to="/recruiter/listings/1" className={linkClass}>Sample listing 1</Link>
      <Link to="/recruiter/listings/1/edit" className={linkClass}>Edit sample listing 1</Link>
    </PlaceholderPage>
  );
}