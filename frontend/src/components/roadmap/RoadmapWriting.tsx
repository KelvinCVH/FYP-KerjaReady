import type { Ref } from "react";
import { LoaderCircle } from "lucide-react";
import { profileCard, sectionIconTile } from "@/components/profile/styles";
import { focusedHeading } from "./styles";

// Shown while the background agent writes the roadmap (generating mockup). The bar has no percentage because the
// agent doesn't report one; under reduced motion it stays still.
export default function RoadmapWriting({ headingRef }: { headingRef: Ref<HTMLHeadingElement> }) {
  return (
    <div className={`${profileCard} flex items-start gap-4`}>
      <div className={`${sectionIconTile} bg-primary-subtle text-primary`}>
        <LoaderCircle aria-hidden="true" className="motion-safe:animate-spin" />
      </div>
      <div className="min-w-0 flex-1">
        <h2 ref={headingRef} tabIndex={-1} className={`${focusedHeading} text-xl font-semibold`}>
          Writing Your Roadmap
        </h2>
        <p className="mt-1 max-w-[65ch] text-base leading-relaxed">
          This usually takes under a minute. Your roadmap is saved when it is ready, so you can leave this page and
          come back.
        </p>
        <div
          role="progressbar"
          aria-label="Writing your roadmap"
          className="mt-4 h-1.5 max-w-md overflow-hidden rounded-md bg-muted"
        >
          <div className="h-full w-1/3 rounded-md bg-primary motion-safe:animate-indeterminate" />
        </div>
      </div>
    </div>
  );
}
