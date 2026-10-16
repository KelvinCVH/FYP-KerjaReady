import { CircleAlert, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { profileCard, sectionIconTile } from "./styles";

type ProfileLoadErrorProps = {
  // HTTP status of the failed request, 0 when it did not reach the API
  status: number;
  message: string;
  onRetry: () => void;
};

// Shown when the profile or the role list fails to load. A 503 means the database is still waking up,
// so it gets a neutral icon; anything else is a system error (DESIGN.md 5.2).
export default function ProfileLoadError({ status, message, onRetry }: ProfileLoadErrorProps) {
  const startingUp = status === 503;

  return (
    <div className={`${profileCard} flex items-start gap-4`}>
      <div className={`${sectionIconTile} ${startingUp ? "bg-muted text-foreground" : "bg-red-50 text-red-700"}`}>
        {startingUp ? <Info aria-hidden="true" /> : <CircleAlert aria-hidden="true" />}
      </div>
      <div className="min-w-0">
        <p role="alert" className="pt-2 text-base font-medium">
          {message}
        </p>
        <Button variant="outline" className="mt-4" onClick={onRetry}>
          Try Again
        </Button>
      </div>
    </div>
  );
}
