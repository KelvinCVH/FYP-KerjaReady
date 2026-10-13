import { useParams } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";

export default function ListingApplicantsPage() {
  const { listingId } = useParams();
  return (
    <PlaceholderPage
      title={`Listing ${listingId} applicants`}
      description="Applicants' resumes and match scores, with accept or reject and a reason."
    />
  );
}