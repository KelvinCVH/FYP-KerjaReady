import { NavLink, useParams } from "react-router";

// Sample IDs to test the routes; replaced by real listings from the API later
const sampleListingIds = ["1", "2", "3"];

export default function JobsPage() {
  const { listingId } = useParams();

  return (
    <div className="grid gap-6 md:grid-cols-[280px_1fr]">
      <section>
        <h1 className="mb-4 text-2xl font-semibold">Jobs</h1>
        <ul className="flex flex-col gap-2">
          {sampleListingIds.map((id) => (
            <li key={id}>
              <NavLink
                to={`/candidate/jobs/${id}`}
                className={({ isActive }) =>
                  `block rounded-md border px-3 py-2 text-sm ${
                    isActive ? "border-gray-900 bg-white" : "border-gray-200 hover:bg-gray-100"
                  }`
                }
              >
                Sample job {id}
              </NavLink>
            </li>
          ))}
        </ul>
      </section>
      <section className="rounded-md border border-gray-200 bg-white p-6">
        {listingId ? (
          <p>Job {listingId}: details, match score and Apply button.</p>
        ) : (
          <p className="text-gray-600">Select a job to see its details.</p>
        )}
      </section>
    </div>
  );
}