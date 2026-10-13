import { useParams } from "react-router";
import PlaceholderPage from "../../components/PlaceholderPage";

export default function EditListingPage() {
  const { listingId } = useParams();
  return <PlaceholderPage title={`Edit listing ${listingId}`} description="Update the job details or close the listing." />;
}