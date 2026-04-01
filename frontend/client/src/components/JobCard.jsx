import React, { useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Building2, ExternalLink } from "lucide-react";
import Card from "./common/Card";
import ScoreBar from "./ScoreBar";
import RoleTypeBadge from "./RoleTypeBadge";
import SkillMatchChips from "./SkillMatchChips";
import ApplyButton from "./ApplyButton";
import { cn } from "../lib/utils";

/**
 * Per guardrails §4: clear visual hierarchy.
 * Role title (large, bold) > company > location/mode > match score.
 * RoleTypeBadge is the first thing the eye hits — top-left.
 * On hover: lift with shadow + apply button highlights.
 */
export default React.memo(function JobCard({
  job,
  skills = [],
  index = 0,
  selectable = false,
  selected = false,
  onSelect,
  className,
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.3 }}
    >
      <Card
        hover
        className={cn(
          "relative group",
          selectable && selected && "ring-2 ring-primary-500 border-primary-200",
          className
        )}
      >
        {/* Top row: badge + match score */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <RoleTypeBadge matchScore={job.match_score || 0} />
          <div className="min-w-[100px]">
            <ScoreBar score={job.match_score || 0} size="sm" />
          </div>
        </div>

        {/* Title + company */}
        <div className="flex items-start gap-3">
          {selectable && (
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onSelect?.()}
              className="mt-1 w-5 h-5 rounded-lg border-slate-300 text-primary-500 focus:ring-primary-200 cursor-pointer"
              aria-label={`Select ${job.title} at ${job.company}`}
            />
          )}
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-bold tracking-tight text-slate-900 leading-snug">
              {job.title}
            </h3>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-sm text-slate-500">
              <span className="inline-flex items-center gap-1">
                <Building2 className="w-3.5 h-3.5" aria-hidden="true" />
                {job.company}
              </span>
              {job.location && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" aria-hidden="true" />
                  {job.location}
                </span>
              )}
              {job.source && (
                <span className="text-xs text-slate-400">
                  via {job.source}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Skill match chips */}
        {skills.length > 0 && (
          <div className="mt-3">
            <SkillMatchChips
              skills={skills}
              jobDescription={job.description || ""}
            />
          </div>
        )}

        {/* Reasoning (AI callout) */}
        {job.reasoning && (
          <div className="ai-callout mt-3 text-sm">
            💡 {job.reasoning}
          </div>
        )}

        {/* Expanded description */}
        {expanded && job.description && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-3 text-sm text-slate-600 leading-relaxed"
          >
            {job.description}
          </motion.div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-100">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
          >
            {expanded ? "Hide details" : "View details"}
          </button>
          <div className="flex-1" />
          <ApplyButton url={job.url} source={job.source} />
        </div>
      </Card>
    </motion.div>
  );
});
