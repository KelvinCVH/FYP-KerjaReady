import { Link } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";

export default function ResumePage() {
  return (
    <PlaceholderPage title="Resume" description="Overview and resume upload.">
      <Link to="/candidate/resume/target-role" className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100">
        Next: select target role
      </Link>
    </PlaceholderPage>
  );
}