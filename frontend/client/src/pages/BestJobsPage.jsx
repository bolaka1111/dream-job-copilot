import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Trophy, Star, TrendingUp } from "lucide-react";
import Card from "../components/common/Card";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import ScoreBar from "../components/ScoreBar";
import StarRating from "../components/StarRating";
import RoleTypeBadge from "../components/RoleTypeBadge";
import SkillMatchChips from "../components/SkillMatchChips";
import ApplyButton from "../components/ApplyButton";
import { usePipeline } from "../hooks/usePipeline";

export default function BestJobsPage() {
  const { state } = usePipeline();
  const navigate = useNavigate();
  const bestJobs = state.bestJobs || state.refinedJobs || [];
  const rawReviews = state.reviews || [];
  const reviewedJobs = state.reviewedJobs || [];
  const skills = state.resumeProfile?.skills || [];

  // Build a company -> review lookup from reviewedJobs or reviews
  const reviewMap = React.useMemo(() => {
    const map = {};
    // reviewedJobs is [{job, review}, ...]
    for (const item of reviewedJobs) {
      if (item?.review) {
        const key = (item.job?.company || item.review?.company || "").toLowerCase();
        if (key) map[key] = item.review;
      }
    }
    // Also check reviews array (may be same shape)
    for (const item of rawReviews) {
      if (item?.review) {
        const key = (item.job?.company || item.review?.company || "").toLowerCase();
        if (key && !map[key]) map[key] = item.review;
      } else if (item?.company) {
        const key = item.company.toLowerCase();
        if (key && !map[key]) map[key] = item;
      }
    }
    return map;
  }, [rawReviews, reviewedJobs]);

  // Skeleton
  if (!bestJobs.length && state.status === "running") {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
        <div className="skeleton h-8 w-64" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-64" />
        ))}
      </div>
    );
  }

  // Empty
  if (!bestJobs.length) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="text-5xl">🏆</div>
        <h2 className="font-display text-xl font-bold text-slate-900">No refined picks yet</h2>
        <p className="text-sm text-slate-500">Complete the preferences step to see your best matches.</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto px-4 py-10 space-y-6"
    >
      <div>
        <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <Trophy className="w-6 h-6 text-amber-500" aria-hidden="true" />
          Best Matches
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          AI-refined after your preferences — these are your strongest
          opportunities
        </p>
      </div>

      <div className="space-y-6">
        {bestJobs.map((job, i) => {
          return (
            <motion.div
              key={`${job.title}-${job.company}-${i}`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <Card hover className="space-y-4">
                {(() => {
                  const review = reviewMap[(job.company || "").toLowerCase()];
                  const reviewRating = review?.rating ?? 0;
                  const reviewPros = Array.isArray(review?.pros) ? review.pros.join("; ") : (review?.pros || "");
                  const reviewCons = Array.isArray(review?.cons) ? review.cons.join("; ") : (review?.cons || "");
                  const reviewSummary = review?.summary || "";
                  const reviewCount = review?.review_count ?? 0;
                  return (
                    <>
                {/* Top row */}
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-display text-lg font-bold text-slate-900">
                        {job.title}
                      </h3>
                      <RoleTypeBadge matchScore={job.match_score} />
                    </div>
                    <p className="text-sm text-slate-600">
                      {job.company}
                      {job.location && ` · ${job.location}`}
                    </p>
                  </div>
                  <div className="flex-shrink-0 w-40">
                    <ScoreBar score={job.match_score || 0} />
                  </div>
                </div>

                {/* Skills */}
                <SkillMatchChips skills={skills} jobDescription={job.description || ""} />

                {/* AI reasoning */}
                {job.reasoning && (
                  <div className="ai-callout text-sm">{job.reasoning}</div>
                )}

                {/* Review section */}
                {review && reviewRating > 0 && (
                  <div className="border-t border-slate-100 pt-4 space-y-2">
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-amber-500" aria-hidden="true" />
                      <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        Employee Reviews
                      </span>
                    </div>
                    <div className="grid sm:grid-cols-3 gap-3">
                      <div>
                        <StarRating
                          rating={reviewRating}
                          reviewCount={reviewCount}
                        />
                      </div>
                      {reviewPros && (
                        <div>
                          <Badge color="emerald" className="mb-1">Pros</Badge>
                          <p className="text-xs text-slate-600 line-clamp-2">
                            {reviewPros}
                          </p>
                        </div>
                      )}
                      {reviewCons && (
                        <div>
                          <Badge color="rose" className="mb-1">Cons</Badge>
                          <p className="text-xs text-slate-600 line-clamp-2">
                            {reviewCons}
                          </p>
                        </div>
                      )}
                    </div>
                    {reviewSummary && (
                      <p className="text-xs text-slate-500 italic">
                        "{reviewSummary}"
                      </p>
                    )}
                  </div>
                )}

                {/* Growth insight */}
                {job.growth_potential && (
                  <div className="flex items-start gap-2 text-xs text-slate-500">
                    <TrendingUp className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <span>{job.growth_potential}</span>
                  </div>
                )}

                {/* Apply */}
                {job.url && <ApplyButton url={job.url} portal={job.portal} />}
              </>
                  );
                })()}
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Continue */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={() => navigate("/preferences")}
          className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          ← Adjust preferences
        </button>
        <Button
          icon={ArrowRight}
          onClick={() => navigate("/enhanced-resumes")}
          disabled={!state.enhancedResumes?.length}
        >
          View Enhanced Resumes
        </Button>
      </div>
    </motion.div>
  );
}
