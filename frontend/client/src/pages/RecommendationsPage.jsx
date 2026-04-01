import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, CheckSquare, Square } from "lucide-react";
import JobCard from "../components/JobCard";
import Button from "../components/common/Button";
import { usePipeline } from "../hooks/usePipeline";

export default function RecommendationsPage() {
  const { state, dispatch } = usePipeline();
  const navigate = useNavigate();
  const recs = state.recommendations || [];
  const skills = state.resumeProfile?.skills || [];

  const [selected, setSelected] = useState(() => {
    // Default: select all
    return state.selectedJobs?.length ? state.selectedJobs : recs.map((_, i) => i);
  });

  useEffect(() => {
    if (!state.selectedJobs?.length && recs.length) {
      setSelected(recs.map((_, i) => i));
    }
  }, [recs]);

  const toggleSelect = (idx) => {
    setSelected((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  const selectAll = () => setSelected(recs.map((_, i) => i));
  const deselectAll = () => setSelected([]);

  const handleContinue = () => {
    dispatch({ type: "SET_SELECTED_JOBS", indices: selected });
    navigate("/preferences");
  };

  // Skeleton
  if (!recs.length && state.status === "running") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        <div className="skeleton h-8 w-64" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-44" />
        ))}
      </div>
    );
  }

  // Empty state
  if (!recs.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-md mx-auto px-4 py-20 text-center space-y-4"
      >
        <div className="text-5xl">🎯</div>
        <h2 className="font-display text-xl font-bold text-slate-900">
          No recommendations yet
        </h2>
        <p className="text-sm text-slate-500">
          We need more data to make picks — try going back to search.
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto px-4 py-10 space-y-6"
    >
      <div>
        <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900">
          Top Recommendations
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          AI-curated picks from {state.jobResults?.length || 0} results — select
          the roles you love
        </p>
      </div>

      {/* Bulk actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={selectAll}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
        >
          <CheckSquare className="w-4 h-4" /> Select All
        </button>
        <button
          onClick={deselectAll}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          <Square className="w-4 h-4" /> Deselect All
        </button>
        <span className="text-xs text-slate-400">
          {selected.length} of {recs.length} selected
        </span>
      </div>

      {/* Recommendation cards — staggered entrance per guardrails §2 */}
      <div className="space-y-4">
        {recs.map((job, i) => (
          <JobCard
            key={`${job.title}-${job.company}-${i}`}
            job={job}
            skills={skills}
            index={i}
            selectable
            selected={selected.includes(i)}
            onSelect={() => toggleSelect(i)}
          />
        ))}
      </div>

      {/* Continue */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={() => navigate("/job-search")}
          className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          ← Back to all results
        </button>
        <Button
          icon={ArrowRight}
          onClick={handleContinue}
          disabled={selected.length === 0}
        >
          Continue to Preferences
        </Button>
      </div>
    </motion.div>
  );
}
