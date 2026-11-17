import { Info } from "lucide-react";
import type { ResumeRatings as Ratings } from "@/lib/resumeApi";
import { RUBRIC, RUBRIC_SECTIONS, type RubricCriterion } from "@/lib/rubric";
import CriterionCard from "./CriterionCard";
import { LanguageErrorList, WorkLinkEvidence } from "./CriterionEvidence";

// What the checker found for a criterion, if anything
function evidenceFor(criterion: RubricCriterion, ratings: Ratings) {
  if (criterion.key === "a1" && ratings.a1_work_link) return <WorkLinkEvidence link={ratings.a1_work_link} />;
  if (criterion.key === "b2" && ratings.b2_errors.length > 0) {
    return <LanguageErrorList errors={ratings.b2_errors} headingId={`criterion-${criterion.key}-errors`} />;
  }
  return null;
}

// Every criterion's level against rubric v1.0, by section. No overall score: each criterion stands alone.
export default function ResumeRatings({ ratings }: { ratings: Ratings }) {
  return (
    <div className="min-w-0">
      <p className="flex items-start gap-2 text-sm text-muted-foreground">
        <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
        These ratings describe what your resume shows, measured against the KerjaReady rubric. They come from an
        automated model and do not measure your ability.
      </p>

      {RUBRIC_SECTIONS.map((section) => (
        <section key={section.key} aria-labelledby={`rubric-${section.key}-heading`} className="mt-8">
          <h2 id={`rubric-${section.key}-heading`} className="text-xl font-semibold text-balance">
            {section.title}
          </h2>
          <div className="mt-4 space-y-4">
            {RUBRIC.filter((criterion) => criterion.section === section.key).map((criterion) => (
              <CriterionCard key={criterion.key} criterion={criterion} level={ratings[criterion.key]}>
                {evidenceFor(criterion, ratings)}
              </CriterionCard>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
