import { ArrowRight } from "lucide-react";
import StatusBadge from "@/components/StatusBadge";
import { STATUS } from "@/lib/status";

type ExampleSkill = {
  name: string;
  evidenced: boolean;
  evidence?: string;
};

const exampleSkills: ExampleSkill[] = [
  {
    name: "SQL",
    evidenced: true,
    evidence: "Wrote SQL queries to clean and join 50,000 sales records for a monthly report.",
  },
  { name: "Python", evidenced: true },
  { name: "Data Visualisation", evidenced: true },
  { name: "Excel", evidenced: true },
  { name: "Power BI", evidenced: false },
  { name: "Statistics", evidenced: false },
];

const evidencedCount = exampleSkills.filter((skill) => skill.evidenced).length;

export default function ExampleResultCard() {
  return (
    <figure className="w-full max-w-lg lg:justify-self-end">
      <figcaption className="mb-2 text-sm text-muted-foreground">Example result</figcaption>

      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
          <div>
            <p className="text-sm text-muted-foreground">Target role</p>
            <p className="text-lg font-medium">Data Analyst</p>
          </div>
          <div className="text-right">
            <p className="whitespace-nowrap font-mono text-2xl font-semibold tabular-nums">
              {evidencedCount} of {exampleSkills.length}
            </p>
            <p className="text-sm text-muted-foreground">skills evidenced</p>
          </div>
        </div>

        <ul className="px-5 py-2">
          {exampleSkills.map((skill) => (
            <li key={skill.name} className="py-2.5">
              <div className="flex items-center justify-between gap-4">
                <span className="min-w-0 text-sm font-medium">{skill.name}</span>
                <StatusBadge {...(skill.evidenced ? STATUS.evidenced : STATUS.notEvidenced)} />
              </div>
              {skill.evidence && (
                <blockquote className="mt-2 border-l-2 border-border pl-3 text-sm text-muted-foreground">
                  “{skill.evidence}”
                </blockquote>
              )}
            </li>
          ))}
        </ul>

        <div className="flex items-center justify-between gap-4 border-t border-border px-5 py-4 text-sm">
          <p className="min-w-0 text-muted-foreground">
            Next on your roadmap: <span className="font-medium text-foreground">Power BI</span>
          </p>
          <ArrowRight aria-hidden="true" className="size-4 text-primary" />
        </div>
      </div>
    </figure>
  );
}
