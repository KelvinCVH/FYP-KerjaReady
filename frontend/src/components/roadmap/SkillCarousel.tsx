import { cn } from "cn";
import type { useSnapCarousel } from "@/hooks/useSnapCarousel";
import type { SkillMilestone } from "@/lib/roadmapApi";
import SkillCard from "./SkillCard";
import StepMarker from "./StepMarker";
import { skillCardWidth } from "./styles";

type SkillCarouselProps = {
  id: string;
  milestones: SkillMilestone[];
  carousel: ReturnType<typeof useSnapCarousel>;
  selected: number | null;
  panelId: string;
  buttonId: (index: number) => string;
  onToggle: (index: number) => void;
};

// The skills in demand order on a numbered timeline, in a scroll-snap row: 3 cards across on a wide page, 1 and a
// peek on a phone. It is a focusable region, so the arrow keys scroll it, and a mouse can drag it.
// contain-inline-size keeps the row of 260px cards out of the page's minimum width: without it, the layout's flex
// <main> grows to fit all 6 cards and the whole page scrolls sideways below about 1100px. relative makes the
// scroller the containing block of the cards' sr-only text, so text in cards scrolled out of view doesn't widen the
// page either.
export default function SkillCarousel({
  id,
  milestones,
  carousel,
  selected,
  panelId,
  buttonId,
  onToggle,
}: SkillCarouselProps) {
  const { scrollerRef, scrollerProps, dragging, view } = carousel;
  const scrollable = !(view.atStart && view.atEnd);
  const last = milestones.length - 1;

  return (
    <div
      id={id}
      ref={scrollerRef}
      role="region"
      aria-label="Skills to build"
      tabIndex={0}
      {...scrollerProps}
      className={cn(
        "relative overflow-x-auto overscroll-x-contain rounded-xl outline-none contain-inline-size [scrollbar-width:none] focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background [&::-webkit-scrollbar]:hidden",
        dragging ? "cursor-grabbing snap-none select-none" : "snap-x snap-mandatory",
        scrollable && !dragging && "cursor-grab",
      )}
    >
      <ol className="flex gap-4">
        {milestones.map((milestone, index) => (
          <li key={index} data-carousel-item className={`${skillCardWidth} flex shrink-0 snap-start flex-col`}>
            {/* The timeline: a numbered marker over each card, joined across the gap to the next */}
            <div aria-hidden="true" className="relative mb-3 flex h-7 justify-center">
              {index > 0 && (
                <span className="absolute top-1/2 right-1/2 -left-2 h-0.5 -translate-y-1/2 bg-zinc-300" />
              )}
              {index < last && (
                <span className="absolute top-1/2 -right-2 left-1/2 h-0.5 -translate-y-1/2 bg-zinc-300" />
              )}
              <StepMarker step={index + 1} />
            </div>
            <SkillCard
              milestone={milestone}
              step={index + 1}
              selected={selected === index}
              panelId={panelId}
              buttonId={buttonId(index)}
              onToggle={() => onToggle(index)}
            />
          </li>
        ))}
      </ol>
    </div>
  );
}
