import { Link } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";

export default function SelectTargetRolePage() {
  return (
    <PlaceholderPage title="Select target role" description="Choose the role your resume is assessed against.">
      <Link to="/candidate/resume/result" className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100">
        Next: view result
      </Link>
    </PlaceholderPage>
  );
}