import { useEffect, useId, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { profileCard } from "@/components/profile/styles";
import { Button } from "@/components/ui/button";
import { scrollBehaviour, useSnapCarousel, type CarouselView } from "@/hooks/useSnapCarousel";
import type { SkillMilestone } from "@/lib/roadmapApi";
import SkillCarousel from "./SkillCarousel";
import SkillDetailsPanel from "./SkillDetailsPanel";

// The panel counts as on screen while its top is above this distance from the bottom of the window
const PANEL_VISIBLE_PX = 96;

// "Skills 1–3 of 6", or "Skill 6 of 6" when one card fills the view
function counterText({ first, last }: CarouselView, total: number) {
  return first === last ? `Skill ${first} of ${total}` : `Skills ${first}–${last} of ${total}`;
}

// The skills not evidenced in the resume, in demand order, with the details of the one selected below them.
// The page keys it by run, so a new roadmap starts with no skill selected and the carousel at the start.
export default function BuildSkillsSection({ milestones }: { milestones: SkillMilestone[] }) {
  const baseId = useId();
  const headingId = `${baseId}-heading`;
  const scrollerId = `${baseId}-skills`;
  const panelId = `${baseId}-details`;
  const buttonId = (index: number) => `${baseId}-button-${index}`;

  const total = milestones.length;
  const carousel = useSnapCarousel(total);
  const { view } = carousel;
  // One card at most is selected, and none at first
  const [selected, setSelected] = useState<number | null>(null);

  // Focus stays on the card's button (a disclosure). The panel is brought into view only when it is off screen.
  useEffect(() => {
    if (selected === null) return;
    const panel = document.getElementById(panelId);
    if (!panel) return;
    const { top } = panel.getBoundingClientRect();
    if (top >= 0 && top <= window.innerHeight - PANEL_VISIBLE_PX) return;
    panel.scrollIntoView({ block: "nearest", behavior: scrollBehaviour() });
  }, [selected, panelId]);

  function toggle(index: number) {
    setSelected((current) => (current === index ? null : index));
  }

  // Close returns focus to the button that opened the panel
  function close() {
    if (selected === null) return;
    const index = selected;
    setSelected(null);
    document.getElementById(buttonId(index))?.focus();
  }

  const current = selected === null ? null : milestones[selected];

  return (
    <section aria-labelledby={headingId}>
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between md:gap-8">
        <div className="min-w-0">
          <h2 id={headingId} className="text-xl font-semibold">
            Build These Skills
          </h2>
          {total > 0 && (
            <p className="mt-1 max-w-[65ch] text-sm text-muted-foreground">
              The skills not evidenced in your resume that the most postings ask for, in that order. Drag or use the
              arrows to see them all, then select View Details on a skill.
            </p>
          )}
        </div>

        {total > 0 && (
          <div className="flex shrink-0 items-center justify-between gap-3 md:justify-end">
            <p aria-live="polite" className="text-sm text-muted-foreground tabular-nums">
              {counterText(view, total)}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="icon"
                aria-label="Previous skills"
                aria-controls={scrollerId}
                aria-disabled={view.atStart || undefined}
                className="aria-disabled:pointer-events-none aria-disabled:opacity-50"
                onClick={() => {
                  if (!view.atStart) carousel.scrollByCard(-1);
                }}
              >
                <ChevronLeft aria-hidden="true" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                aria-label="Next skills"
                aria-controls={scrollerId}
                aria-disabled={view.atEnd || undefined}
                className="aria-disabled:pointer-events-none aria-disabled:opacity-50"
                onClick={() => {
                  if (!view.atEnd) carousel.scrollByCard(1);
                }}
              >
                <ChevronRight aria-hidden="true" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {total === 0 ? (
        <div className={`${profileCard} mt-4`}>
          <p className="text-base">Your resume evidences every skill in this role’s profile.</p>
        </div>
      ) : (
        <>
          <div className="mt-5">
            <SkillCarousel
              id={scrollerId}
              milestones={milestones}
              carousel={carousel}
              selected={selected}
              panelId={panelId}
              buttonId={buttonId}
              onToggle={toggle}
            />
          </div>
          {current && selected !== null && (
            <div className="mt-6">
              <SkillDetailsPanel
                key={selected}
                id={panelId}
                milestone={current}
                step={selected + 1}
                total={total}
                onClose={close}
              />
            </div>
          )}
        </>
      )}
    </section>
  );
}
