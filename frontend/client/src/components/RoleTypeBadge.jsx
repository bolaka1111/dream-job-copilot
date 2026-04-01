import React from "react";
import { cn } from "../lib/utils";
import { Star, CheckCircle, TrendingUp } from "lucide-react";
import Badge from "./common/Badge";

/**
 * Role type badge — Dream / Safe / Stretch. Per guardrails §4:
 * "The first thing the eye hits — top-left of card."
 */
export default function RoleTypeBadge({ matchScore, className }) {
  const pct = matchScore * 100;

  if (pct >= 80) {
    return (
      <Badge color="emerald" className={cn("gap-1", className)}>
        <CheckCircle className="w-3 h-3" aria-hidden="true" /> Safe Match
      </Badge>
    );
  }
  if (pct >= 50) {
    return (
      <Badge color="amber" className={cn("gap-1", className)}>
        <Star className="w-3 h-3" aria-hidden="true" /> Dream Role
      </Badge>
    );
  }
  return (
    <Badge color="violet" className={cn("gap-1", className)}>
      <TrendingUp className="w-3 h-3" aria-hidden="true" /> Stretch Role
    </Badge>
  );
}
