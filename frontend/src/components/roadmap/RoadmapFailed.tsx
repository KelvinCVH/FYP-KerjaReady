import type { Ref } from "react";
import { CircleAlert } from "lucide-react";
import FormAlert from "@/components/auth/FormAlert";
import LoadingButton from "@/components/LoadingButton";
import { profileCard, sectionIconTile } from "@/components/profile/styles";
import { focusedHeading } from "./styles";

type RoadmapFailedProps = {
  headingRef: Ref<HTMLHeadingElement>;
  // Why the last Try Again (or the first start) failed, from the API; null when the run itself failed
  error: string | null;
  starting: boolean;
  onRetry: () => void;
};

// The run failed, timed out, or could not start
export default function RoadmapFailed({ headingRef, error, starting, onRetry }: RoadmapFailedProps) {
  return (
    <div className={`${profileCard} flex items-start gap-4`}>
      <div className={`${sectionIconTile} bg-red-50 text-red-700`}>
        <CircleAlert aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <h2 ref={headingRef} tabIndex={-1} className={`${focusedHeading} text-xl font-semibold`}>
          We Couldn’t Write Your Roadmap
        </h2>
        <p className="mt-1 text-base leading-relaxed text-muted-foreground">
          Please try again. If it keeps failing, try again later.
        </p>
        {error && (
          <div className="mt-4">
            <FormAlert message={error} />
          </div>
        )}
        <LoadingButton className="mt-5" pending={starting} pendingLabel="Starting…" onClick={onRetry}>
          Try Again
        </LoadingButton>
      </div>
    </div>
  );
}
