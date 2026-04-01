import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Search, SlidersHorizontal } from "lucide-react";
import JobCard from "../components/JobCard";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import { usePipeline } from "../hooks/usePipeline";

export default function JobSearchPage() {
  const { state } = usePipeline();
  const navigate = useNavigate();
  const jobs = state.jobResults || [];
  const skills = state.resumeProfile?.skills || [];

  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("match");
  const [showFilters, setShowFilters] = useState(false);

  // Skeleton — guardrails §3
  if (!jobs.length && state.status === "running") {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
        <div className="skeleton h-8 w-72" />
        <div className="grid md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-52" />
          ))}
        </div>
      </div>
    );
  }

  // Empty state — guardrails §3
  if (!jobs.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-md mx-auto px-4 py-20 text-center space-y-4"
      >
        <div className="text-5xl">🔍</div>
        <h2 className="font-display text-xl font-bold text-slate-900">
          No roles found yet
        </h2>
        <p className="text-sm text-slate-500">
          We're still searching — this might take a moment. Try widening your
          search scope if results are slow to appear.
        </p>
      </motion.div>
    );
  }

  const filteredJobs = useMemo(() => {
    let result = [...jobs];

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (j) =>
          j.title?.toLowerCase().includes(term) ||
          j.company?.toLowerCase().includes(term) ||
          j.location?.toLowerCase().includes(term)
      );
    }

    if (sortBy === "match") {
      result.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
    } else if (sortBy === "company") {
      result.sort((a, b) => (a.company || "").localeCompare(b.company || ""));
    }

    return result;
  }, [jobs, searchTerm, sortBy]);

  // Animate count — guardrails §5
  const countDisplay = `${filteredJobs.length} role${filteredJobs.length !== 1 ? "s" : ""} found`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto px-4 py-10 space-y-6"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900">
            Job Search Results
          </h2>
          <motion.p
            key={countDisplay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-sm text-slate-500 mt-1"
          >
            {countDisplay}
          </motion.p>
        </div>

        <div className="flex items-center gap-2">
          <Input
            placeholder="Search roles, companies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            icon={Search}
            className="w-60"
          />
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-2.5 rounded-2xl border border-slate-200 hover:bg-slate-50 transition-colors"
            aria-label="Toggle filters"
          >
            <SlidersHorizontal className="w-4 h-4 text-slate-500" />
          </button>
        </div>
      </div>

      {/* Sort bar */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="flex flex-wrap gap-2"
        >
          {[
            { key: "match", label: "Match score" },
            { key: "company", label: "Company A-Z" },
          ].map((opt) => (
            <button
              key={opt.key}
              onClick={() => setSortBy(opt.key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                sortBy === opt.key
                  ? "bg-primary-100 text-primary-700"
                  : "bg-slate-100 text-slate-500 hover:bg-slate-200"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </motion.div>
      )}

      {/* Job grid */}
      <div className="grid md:grid-cols-2 gap-4">
        {filteredJobs.map((job, i) => (
          <JobCard key={`${job.title}-${job.company}-${i}`} job={job} skills={skills} index={i} />
        ))}
      </div>

      {/* Continue */}
      <div className="flex justify-end pt-4">
        <Button
          icon={ArrowRight}
          onClick={() => navigate("/recommendations")}
          disabled={!state.recommendations?.length}
        >
          See What's Recommended
        </Button>
      </div>
    </motion.div>
  );
}
