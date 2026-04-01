import React from "react";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";

/**
 * Score bar with animated fill. Colour coded per guardrails §4.
 * Green >80%, Amber 50-80%, Rose <50%.
 */
export default React.memo(function ScoreBar({
  score,
  showLabel = true,
  size = "md",
  className,
}) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80
      ? "bg-emerald-500"
      : pct >= 50
        ? "bg-amber-400"
        : "bg-rose-400";

  const heights = { sm: "h-1.5", md: "h-2.5", lg: "h-3.5" };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className={cn("score-bar flex-1", heights[size])}>
        <motion.div
          className={cn("score-bar-fill", color, heights[size])}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 60, damping: 15, delay: 0.2 }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-bold text-slate-700 tabular-nums min-w-[40px] text-right">
          {pct}%
        </span>
      )}
    </div>
  );
});
