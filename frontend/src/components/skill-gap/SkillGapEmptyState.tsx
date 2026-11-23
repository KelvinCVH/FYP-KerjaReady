import type { ReactNode } from "react";
import { cn } from "cn";
import { profileCard, sectionIconTile } from "@/components/profile/styles";

type SkillGapEmptyStateProps = {
  // A lucide icon with aria-hidden
  icon: ReactNode;
  // "brand": an emerald tile, decorative. "neutral": zinc, for a state such as an unfinished assessment.
  tone?: "brand" | "neutral";
  // One sentence saying what will appear and how
  children: ReactNode;
  // The one primary action
  action: ReactNode;
};

// Why there is no skill gap to show yet, with the one action that fixes it (no-role and no-resume mockups)
export default function SkillGapEmptyState({ icon, tone = "brand", children, action }: SkillGapEmptyStateProps) {
  return (
    <div className={`${profileCard} flex flex-col items-center px-6 py-12 text-center`}>
      <div
        className={cn(
          sectionIconTile,
          "size-12 [&_svg]:size-6",
          tone === "brand" ? "bg-primary-subtle text-primary" : "bg-muted text-foreground",
        )}
      >
        {icon}
      </div>
      <p className="mt-4 max-w-md text-base leading-relaxed text-balance">{children}</p>
      <div className="mt-5">{action}</div>
    </div>
  );
}
