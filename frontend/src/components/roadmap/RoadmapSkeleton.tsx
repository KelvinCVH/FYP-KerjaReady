import { cn } from "cn";
import { profileCard } from "@/components/profile/styles";
import { Skeleton } from "@/components/ui/skeleton";
import StepMarker from "./StepMarker";
import { skillCardWidth } from "./styles";

type RoadmapSkeletonProps = {
  // Include the context card, for the first load. The writing state shows the real one above.
  withContext?: boolean;
  // No pulse, for the writing state, where the bar already shows progress
  still?: boolean;
};

// Placeholders in the shape of the roadmap: 2 resume step cards, then the skills timeline and cards
export default function RoadmapSkeleton({ withContext = false, still = false }: RoadmapSkeletonProps) {
  function bone(className: string) {
    return <Skeleton className={cn(className, still && "animate-none")} />;
  }

  return (
    <div aria-hidden="true">
      {withContext && (
        <div className={`${profileCard} mb-6 grid gap-x-10 gap-y-5 py-5 sm:grid-cols-2 sm:items-center`}>
          <div className="flex items-center gap-4">
            {bone("size-10 shrink-0 rounded-lg")}
            <div className="min-w-0 flex-1 space-y-2">
              {bone("h-4 w-20")}
              {bone("h-6 w-40 max-w-full")}
              {bone("h-4 w-56 max-w-full")}
            </div>
          </div>
          <div className="space-y-2">
            {bone("h-4 w-16")}
            {bone("h-5 w-48 max-w-full")}
            {bone("h-4 w-32")}
          </div>
        </div>
      )}

      {bone("h-6 w-48")}
      <div className="mt-4 grid gap-5 md:grid-cols-2">
        {[0, 1].map((card) => (
          <div key={card} className={profileCard}>
            {bone("h-5 w-36")}
            <div className="mt-4 space-y-2">
              {bone("h-3.5 w-full")}
              {bone("h-3.5 w-4/5")}
            </div>
            {bone("mt-5 h-20 w-full rounded-lg")}
          </div>
        ))}
      </div>

      {bone("mt-10 h-6 w-44")}
      {/* contain-inline-size: as in SkillCarousel, the cards mustn't widen the page */}
      <div className="mt-5 flex gap-4 overflow-hidden contain-inline-size">
        {[0, 1, 2].map((card) => (
          <div key={card} className={`${skillCardWidth} shrink-0`}>
            <div className="relative mb-3 flex h-7 justify-center">
              {card > 0 && <span className="absolute top-1/2 right-1/2 -left-2 h-0.5 -translate-y-1/2 bg-border" />}
              <span className="absolute top-1/2 -right-2 left-1/2 h-0.5 -translate-y-1/2 bg-border" />
              <StepMarker />
            </div>
            <div className="rounded-xl border-2 border-border bg-card p-4">
              <div className="flex items-center gap-3">
                {bone("size-11 shrink-0 rounded-lg")}
                {bone("h-5 w-28")}
              </div>
              <div className="mt-5 space-y-2">
                {bone("h-3.5 w-full")}
                {bone("h-3.5 w-5/6")}
                {bone("h-3.5 w-4/5")}
              </div>
              {bone("mt-8 h-11 w-full rounded-lg")}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
