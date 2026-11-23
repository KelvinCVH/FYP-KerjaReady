type SkillDemandProps = {
  // How many of the role's postings ask for the skill, counted by the API
  postings: number;
  // The same as a share of the role's postings, from 0 to 1
  demandShare: number;
  postingCount: number;
};

// How often the role's postings ask for a skill: a small bar and "14 (27%)".
// The bar is decoration; screen readers hear "Asked in 14 of 52 postings (27%)".
export default function SkillDemand({ postings, demandShare, postingCount }: SkillDemandProps) {
  const percent = Math.round(demandShare * 100);

  return (
    <span className="flex shrink-0 items-center gap-3">
      <span aria-hidden="true" className="hidden h-1.5 w-14 overflow-hidden rounded-md bg-border sm:block">
        <span className="block h-full bg-muted-foreground" style={{ width: `${Math.min(demandShare, 1) * 100}%` }} />
      </span>
      <span className="w-20 text-right text-sm tabular-nums">
        <span className="sr-only">Asked in </span>
        {postings}
        <span className="sr-only"> of {postingCount} postings</span> ({percent}%)
      </span>
    </span>
  );
}
