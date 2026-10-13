import type { ReactNode } from "react";
import { Link } from "react-router";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import StatusBadge from "@/components/StatusBadge";
import { STATUS } from "@/lib/status";
import FadeUp from "./FadeUp";
import { container, sectionSpacing } from "./styles";

const studentFeatures = [
  "Role-aligned resume assessment",
  "Skill gap analysis against Malaysian job postings",
  "Resume recommendations tied to your own words",
  "A learning roadmap and job matches with a match score",
];

const recruiterFeatures = [
  "Post and manage job listings",
  "A match score for every applicant",
  "Resume evidence for each required skill",
  "Accept or reject with a reason the candidate can see",
];

const exampleRoadmap = [
  { skill: "Power BI", task: "Build one dashboard from a public dataset and add it to your resume." },
  { skill: "Statistics", task: "Practise hypothesis testing in a small analysis project." },
];

const exampleApplicants = [
  { name: "Nurul Aina binti Razak", score: 82.4, status: STATUS.submitted },
  { name: "Lim Wei Jie", score: 76.9, status: STATUS.accepted },
  { name: "Arjun Ramasamy", score: 68.3, status: STATUS.submitted },
];

const scoreFormat = new Intl.NumberFormat("en-MY", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

function FeatureList({ items }: { items: string[] }) {
  return (
    <ul className="mt-6 space-y-3">
      {items.map((item) => (
        <li key={item} className="flex items-start gap-3 text-sm">
          <Check aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" />
          {item}
        </li>
      ))}
    </ul>
  );
}

type PanelProps = {
  id: string;
  title: string;
  description: string;
  className: string;
  children: ReactNode;
};

function Panel({ id, title, description, className, children }: PanelProps) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-heading`}
      className={`flex flex-col rounded-xl border p-6 md:p-8 ${className}`}
    >
      <h2 id={`${id}-heading`} className="text-2xl font-semibold tracking-tight">
        {title}
      </h2>
      <p className="mt-3 max-w-[65ch] text-base leading-relaxed text-muted-foreground">
        {description}
      </p>
      {children}
    </section>
  );
}

export default function AudiencePanels() {
  return (
    <div className={sectionSpacing}>
      <FadeUp className={`${container} grid gap-6 md:grid-cols-2`}>
        <Panel
          id="for-students"
          title="For Students"
          description="Understand how your resume reads for the role you want, then work on what is not yet evidenced."
          className="border-primary/20 bg-primary-subtle"
        >
          <FeatureList items={studentFeatures} />

          <figure className="mt-8 rounded-xl border border-border bg-card p-5">
            <figcaption className="text-sm text-muted-foreground">
              Example roadmap for Data Analyst
            </figcaption>
            <ol className="mt-3 space-y-3">
              {exampleRoadmap.map((step, index) => (
                <li key={step.skill} className="flex gap-3">
                  <span
                    aria-hidden="true"
                    className={`flex size-6 shrink-0 items-center justify-center rounded-md text-sm font-medium tabular-nums ${
                      index === 0 ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                    }`}
                  >
                    {index + 1}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{step.skill}</p>
                    <p className="text-sm text-muted-foreground">{step.task}</p>
                  </div>
                </li>
              ))}
            </ol>
          </figure>

          <div className="mt-auto pt-10">
            <Button asChild size="lg">
              <Link to="/register?role=candidate">Assess My Resume</Link>
            </Button>
          </div>
        </Panel>

        <Panel
          id="for-recruiters"
          title="For Recruiters"
          description="Post roles and review applicants with candidate insights that show how each resume aligns with your listing."
          className="border-border bg-card"
        >
          <FeatureList items={recruiterFeatures} />

          <div className="mt-8 overflow-hidden rounded-xl border border-border bg-card">
            <table className="w-full text-sm">
              <caption className="border-b border-border px-4 py-3 text-left text-sm text-muted-foreground md:px-5">
                Example applicants for Junior Data Analyst
              </caption>
              <thead className="sr-only">
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Match score</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {exampleApplicants.map((applicant) => (
                  <tr key={applicant.name}>
                    <th scope="row" className="px-4 py-3 text-left font-medium md:px-5">
                      {applicant.name}
                    </th>
                    <td className="px-2 py-3 text-right font-mono font-semibold tabular-nums">
                      {scoreFormat.format(applicant.score)}
                    </td>
                    <td className="py-3 pr-4 text-right md:pr-5">
                      <StatusBadge {...applicant.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-sm text-muted-foreground">
            Match scores are supporting signals, not a measure of a candidate’s ability.
          </p>

          <div className="mt-auto pt-10">
            <Button asChild variant="outline" size="lg">
              <Link to="/register?role=recruiter">Find Candidates</Link>
            </Button>
          </div>
        </Panel>
      </FadeUp>
    </div>
  );
}
