import { profileCard } from "@/components/profile/styles";
import { Skeleton } from "@/components/ui/skeleton";

const ROW_WIDTHS = ["w-32", "w-24", "w-40", "w-28", "w-36", "w-20"];

function ColumnSkeleton() {
  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <div className="p-4">
        <Skeleton className="h-6 w-56 max-w-full" />
        <Skeleton className="mt-2.5 h-4 w-80 max-w-full" />
      </div>
      <div className="h-9 border-y bg-background" />
      <div className="divide-y">
        {ROW_WIDTHS.map((width) => (
          <div key={width} className="flex items-center justify-between gap-4 px-4 py-3.5">
            <Skeleton className={`h-4 ${width}`} />
            <Skeleton className="h-4 w-32" />
          </div>
        ))}
      </div>
    </div>
  );
}

function Columns() {
  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 lg:items-start">
      <ColumnSkeleton />
      <ColumnSkeleton />
    </div>
  );
}

// The loading mockup's shapes (DESIGN.md 9.3). columnsOnly: just the two columns, while switching resume.
// Decoration only: the page's status message says what is loading.
export default function SkillGapSkeleton({ columnsOnly = false }: { columnsOnly?: boolean }) {
  if (columnsOnly) {
    return (
      <div aria-hidden="true">
        <Columns />
      </div>
    );
  }

  return (
    <div aria-hidden="true">
      <div
        className={`${profileCard} grid gap-x-10 gap-y-5 py-5 sm:grid-cols-[minmax(0,1fr)_auto] lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,22rem)] lg:items-center`}
      >
        <div className="flex items-center gap-4">
          <Skeleton className="size-10 shrink-0 rounded-lg" />
          <div className="min-w-0 flex-1">
            <Skeleton className="h-3.5 w-20" />
            <Skeleton className="mt-2 h-5 w-40" />
            <Skeleton className="mt-2 h-3.5 w-64 max-w-full" />
          </div>
        </div>
        <div>
          <Skeleton className="h-3.5 w-24" />
          <Skeleton className="mt-2 h-7 w-20" />
        </div>
        <div className="sm:col-span-2 lg:col-span-1">
          <Skeleton className="h-3.5 w-14" />
          <Skeleton className="mt-2 h-11 w-full rounded-lg" />
        </div>
      </div>
      <Skeleton className="mt-6 h-4 w-3/4" />
      <div className="mt-6">
        <Columns />
      </div>
    </div>
  );
}
