import type { VariantProps } from "class-variance-authority";
import {
  CircleAlert,
  CircleCheck,
  CircleDashed,
  CircleX,
  Clock,
  LoaderCircle,
  type LucideIcon,
} from "lucide-react";
import type { badgeVariants } from "@/components/ui/badge";
import type { AssessmentStatus } from "@/lib/resumeApi";

export type Status = {
  variant: NonNullable<VariantProps<typeof badgeVariants>["variant"]>;
  icon: LucideIcon;
  label: string;
};

// DESIGN.md Section 5.2: colour is never the only signal, so every status has an icon and a label
export const STATUS = {
  evidenced: { variant: "success", icon: CircleCheck, label: "Evidenced" },
  notEvidenced: { variant: "neutral", icon: CircleDashed, label: "Not evidenced" },
  submitted: { variant: "neutral", icon: Clock, label: "Submitted" },
  accepted: { variant: "success", icon: CircleCheck, label: "Accepted" },
  rejected: { variant: "rejected", icon: CircleX, label: "Rejected" },
} satisfies Record<string, Status>;

const inProgress: Status = { variant: "progress", icon: LoaderCircle, label: "In progress" };

// Where a resume assessment got to, for the Past Assessments list. "Failed" is about processing, not a rating.
export const ASSESSMENT_STATUS: Record<AssessmentStatus, Status> = {
  uploaded: inProgress,
  reading: inProgress,
  rating: inProgress,
  done: { variant: "success", icon: CircleCheck, label: "Assessed" },
  failed: { variant: "error", icon: CircleAlert, label: "Failed" },
  // Clock, as on the timed-out progress card
  timed_out: { variant: "warning", icon: Clock, label: "Timed out" },
};
