import { Badge } from "@/components/ui/badge";
import type { Status } from "@/lib/status";

// Presets for each DESIGN.md Section 5.2 status live in @/lib/status
export default function StatusBadge({ variant, icon: Icon, label }: Status) {
  return (
    <Badge variant={variant}>
      <Icon aria-hidden="true" />
      {label}
    </Badge>
  );
}
