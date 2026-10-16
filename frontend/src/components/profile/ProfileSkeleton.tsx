import { Skeleton } from "@/components/ui/skeleton";
import { profileCard } from "./styles";

// Same shapes as the Target Role and Account Details cards (DESIGN.md 9.3)
export default function ProfileSkeleton() {
  return (
    <div aria-busy="true">
      <p className="sr-only">Loading your profile…</p>
      <div aria-hidden="true" className="space-y-6">
        <div className={profileCard}>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="mt-2 h-4 w-full max-w-md" />
          <div className="mt-5 flex items-start gap-4 border-t pt-6">
            <Skeleton className="size-10 shrink-0 rounded-lg" />
            <div className="min-w-0 flex-1">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="mt-2 h-4 w-full max-w-lg" />
              <Skeleton className="mt-4 h-11 w-44 rounded-lg" />
            </div>
          </div>
        </div>

        <div className={profileCard}>
          <Skeleton className="h-6 w-40" />
          <div className="mt-1 divide-y">
            {["w-56", "w-64", "w-28"].map((valueWidth) => (
              <div key={valueWidth} className="flex h-12.5 items-center">
                <Skeleton className="h-4 w-24 md:mr-16" />
                <Skeleton className={`h-4 ${valueWidth}`} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
