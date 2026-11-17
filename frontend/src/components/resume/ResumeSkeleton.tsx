import { Skeleton } from "@/components/ui/skeleton";
import { profileCard } from "@/components/profile/styles";

// Same shapes as the ratings view: the resume bar, criterion cards and the PDF panel (DESIGN.md 9.3)
export default function ResumeSkeleton() {
  return (
    <div aria-busy="true">
      <p className="sr-only">Loading your resume…</p>
      <div aria-hidden="true">
        <div className={`${profileCard} flex items-center gap-4 py-4`}>
          <Skeleton className="size-10 shrink-0 rounded-lg" />
          <div className="flex-1">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="mt-2 h-4 w-40" />
          </div>
          <Skeleton className="h-11 w-44 rounded-lg" />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div>
            <Skeleton className="h-10 w-full" />
            <Skeleton className="mt-8 h-6 w-28" />
            <div className="mt-4 space-y-4">
              {[0, 1, 2].map((card) => (
                <div key={card} className={profileCard}>
                  <div className="flex justify-between gap-4">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-5 w-28" />
                  </div>
                  <Skeleton className="mt-3 h-4 w-3/4" />
                  <Skeleton className="mt-5 h-4 w-full" />
                  <Skeleton className="mt-2 h-4 w-2/3" />
                </div>
              ))}
            </div>
          </div>
          <div className={`${profileCard} self-start`}>
            <div className="flex justify-between gap-4">
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-5 w-32" />
            </div>
            <Skeleton className="mt-6 h-160 w-full rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}
