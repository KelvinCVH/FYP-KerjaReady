import type { VariantProps } from "class-variance-authority";
import { CircleCheck, CircleDashed, CircleX, Clock, type LucideIcon } from "lucide-react";
import type { badgeVariants } from "@/components/ui/badge";

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
