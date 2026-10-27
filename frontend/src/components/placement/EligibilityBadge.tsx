import { Badge } from "@/components/ui/Badge";
import type { Eligibility } from "@/types/api";

export function EligibilityBadge({ eligibility }: { eligibility: Eligibility | null }) {
  if (!eligibility) return null;
  if (!eligibility.registration_open) return <Badge tone="neutral">Registration closed</Badge>;
  return eligibility.eligible ? (
    <Badge tone="success">Eligible</Badge>
  ) : (
    <Badge tone="danger">Not eligible</Badge>
  );
}
