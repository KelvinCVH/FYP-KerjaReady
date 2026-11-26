import type { ReactNode } from "react";
import { BookOpen, CircleCheck, ExternalLink, Hammer, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { SkillMilestone } from "@/lib/roadmapApi";
import { searchLinks } from "@/lib/roadmapText";
import HighlightedLine from "./HighlightedLine";
import LetterTile from "./LetterTile";
import { minorHeading } from "./styles";

type SkillDetailsPanelProps = {
  id: string;
  milestone: SkillMilestone;
  // 1-based position in demand order, and how many skills there are
  step: number;
  total: number;
  onClose: () => void;
};

// A sub-section with its h4, left out by the caller when it has nothing to show
function Part({ title, icon, children }: { title: string; icon?: ReactNode; children: ReactNode }) {
  return (
    <div>
      <h4 className={`${minorHeading} flex items-center gap-1.5 [&_svg]:size-4 [&_svg]:shrink-0`}>
        {icon}
        {title}
      </h4>
      {children}
    </div>
  );
}

// How to learn the selected skill and show it on a resume, under the carousel (mockup). Every text in it is written
// by AI and shown as plain text. Sub-sections with nothing in them are left out.
export default function SkillDetailsPanel({ id, milestone, step, total, onClose }: SkillDetailsPanelProps) {
  const headingId = `${id}-heading`;
  const { skill, practice_project: project } = milestone;

  return (
    <section
      id={id}
      aria-labelledby={headingId}
      className="rounded-xl border-2 border-zinc-700 bg-card p-5 break-words sm:p-6"
    >
      <div className="flex items-start gap-3">
        <LetterTile skill={skill} selected />
        <div className="min-w-0 flex-1">
          <h3 id={headingId} className="text-lg font-semibold break-words">
            {skill}: How to Learn and Show It
          </h3>
          <p className="text-sm text-muted-foreground">
            Step {step} of {total}
          </p>
        </div>
        <Button variant="outline" size="icon" aria-label={`Close ${skill} details`} onClick={onClose}>
          <X aria-hidden="true" />
        </Button>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2 md:gap-8">
        <div className="min-w-0 space-y-6">
          {milestone.learning_order && (
            <Part title="Suggested Order">
              <p className="mt-1.5 text-sm leading-relaxed">{milestone.learning_order}</p>
            </Part>
          )}

          {milestone.objectives.length > 0 && (
            <Part title="What You Will Be Able to Do">
              <ul className="mt-1.5 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
                {milestone.objectives.map((objective, index) => (
                  <li key={index}>{objective}</li>
                ))}
              </ul>
            </Part>
          )}

          {milestone.key_topics.length > 0 && (
            <Part title="Key Topics" icon={<BookOpen aria-hidden="true" />}>
              <ul className="mt-1.5 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
                {milestone.key_topics.map((topic, index) => (
                  <li key={index}>{topic}</li>
                ))}
              </ul>
            </Part>
          )}

          {milestone.ready_when.length > 0 && (
            <Part title="You Are Ready When">
              <ul className="mt-1.5 space-y-2 text-sm leading-relaxed">
                {milestone.ready_when.map((check, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <CircleCheck aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" />
                    <span className="min-w-0">{check}</span>
                  </li>
                ))}
              </ul>
            </Part>
          )}
        </div>

        <div className="min-w-0 space-y-6">
          {project && (
            <div className="rounded-lg border bg-background p-4">
              <Part title="Practice Project" icon={<Hammer aria-hidden="true" />}>
                <p className="mt-2 font-semibold break-words">{project.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{project.description}</p>
                <p className="mt-3 text-sm leading-relaxed">
                  <span className="font-semibold">Deliverable:</span> {project.deliverable}
                </p>
              </Part>
            </div>
          )}

          {milestone.resume_line && (
            <Part title="Show It on Your Resume">
              <HighlightedLine text={milestone.resume_line} className="mt-1.5 text-sm" />
              <p className="mt-2 text-sm text-muted-foreground">Fill in only results you can show.</p>
            </Part>
          )}

          {milestone.search_terms.length > 0 && (
            <Part title="Find Learning Resources" icon={<Search aria-hidden="true" />}>
              <ul className="mt-1.5 space-y-4">
                {milestone.search_terms.map((term, index) => (
                  <li key={index}>
                    <p className="text-sm text-muted-foreground break-words">“{term}”</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {searchLinks(term).map((link) => (
                        <Button key={link.site} asChild variant="outline" className="text-primary">
                          <a href={link.href} target="_blank" rel="noopener noreferrer" aria-label={link.label}>
                            <span translate="no">{link.site}</span>
                            <ExternalLink aria-hidden="true" className="size-4" />
                          </a>
                        </Button>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            </Part>
          )}
        </div>
      </div>
    </section>
  );
}
