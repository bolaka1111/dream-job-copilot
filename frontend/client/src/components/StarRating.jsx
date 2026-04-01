import React from "react";
import { motion } from "framer-motion";
import { Star } from "lucide-react";
import { cn } from "../lib/utils";

/**
 * Animated star rating display. Per guardrails §2: animate on first render.
 */
export default React.memo(function StarRating({
  rating,
  maxRating = 5,
  reviewCount,
  className,
}) {
  const fullStars = Math.floor(rating);
  const partialFill = rating - fullStars;

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <div className="flex gap-0.5">
        {Array.from({ length: maxRating }, (_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08, type: "spring", stiffness: 200 }}
          >
            <Star
              className={cn(
                "w-4 h-4",
                i < fullStars
                  ? "fill-amber-400 text-amber-400"
                  : i === fullStars && partialFill > 0
                    ? "fill-amber-400/50 text-amber-400"
                    : "fill-slate-200 text-slate-200"
              )}
              aria-hidden="true"
            />
          </motion.div>
        ))}
      </div>
      <span className="text-sm font-bold text-slate-700">
        {rating.toFixed(1)}/{maxRating}
      </span>
      {reviewCount !== undefined && (
        <span className="text-xs text-slate-400">
          ({reviewCount.toLocaleString()} reviews)
        </span>
      )}
    </div>
  );
});
