import React from "react";
import { cn } from "../lib/utils";
import Badge from "./common/Badge";

/**
 * Inline skill match chips — emerald for matched, rose for missing.
 * Per guardrails §4: overflow behind "+N more" chip.
 */
export default React.memo(function SkillMatchChips({
  skills = [],
  jobDescription = "",
  maxVisible = 6,
  className,
}) {
  // Simple matching: check if each skill appears in the job description
  const matched = [];
  const missing = [];

  skills.forEach((skill) => {
    if (jobDescription.toLowerCase().includes(skill.toLowerCase())) {
      matched.push(skill);
    } else {
      missing.push(skill);
    }
  });

  const allChips = [
    ...matched.map((s) => ({ name: s, match: true })),
    ...missing.slice(0, 3).map((s) => ({ name: s, match: false })),
  ];

  const visible = allChips.slice(0, maxVisible);
  const remaining = allChips.length - visible.length;

  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {visible.map((chip) => (
        <Badge
          key={chip.name}
          color={chip.match ? "emerald" : "rose"}
        >
          {chip.match ? "✓" : "✗"} {chip.name}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge color="default">+{remaining} more</Badge>
      )}
    </div>
  );
});
