import { useId } from "react";
import type { ResumeStep } from "@/lib/roadmapApi";
import ResumeStepCard from "./ResumeStepCard";

// The lowest-rated assessment criteria (up to 2), side by side from 768px. The page leaves it out when there are none.
export default function ImproveResumeSection({ steps }: { steps: ResumeStep[] }) {
  const headingId = useId();

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="text-xl font-semibold">
        Improve Your Resume
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Your lowest-rated assessment criteria, and how to reach the next level.
      </p>
      <div className="mt-4 grid grid-cols-1 gap-5 md:grid-cols-2">
        {steps.map((step, index) => (
          <ResumeStepCard key={index} step={step} />
        ))}
      </div>
    </section>
  );
}
