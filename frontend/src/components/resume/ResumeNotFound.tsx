import { Link } from "react-router";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import { Button } from "@/components/ui/button";

// The same text as the API's 404, used for a link to a resume that is missing, not theirs or not a resume id
const NOT_FOUND_MESSAGE = "We couldn’t find that resume.";

// Trying again can't bring the resume back, so the action leads to the latest one instead
export default function ResumeNotFound({ message = NOT_FOUND_MESSAGE }: { message?: string }) {
  return (
    <ProfileLoadError
      status={404}
      message={message}
      action={
        <Button asChild variant="outline">
          <Link to="/candidate/resume">View Latest</Link>
        </Button>
      }
    />
  );
}
