import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import confetti from "canvas-confetti";
import {
  PartyPopper,
  CheckCircle2,
  Circle,
  ExternalLink,
  Download,
  FileText,
  Mail,
} from "lucide-react";
import Card from "../components/common/Card";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import ApplyButton from "../components/ApplyButton";
import RoleTypeBadge from "../components/RoleTypeBadge";
import ScoreBar from "../components/ScoreBar";
import { usePipeline } from "../hooks/usePipeline";

export default function ApplyHubPage() {
  const { state, triggerApply, toggleChecklist } = usePipeline();
  const navigate = useNavigate();
  const bestJobs = state.bestJobs || state.refinedJobs || [];
  const resumes = state.enhancedResumes || [];
  const letters = state.coverLetters || [];
  const applications = state.applications || [];

  // Celebration confetti — guardrails §5
  useEffect(() => {
    if (bestJobs.length > 0) {
      confetti({
        particleCount: 60,
        spread: 80,
        origin: { y: 0.4 },
        colors: ["#10B981", "#6366F1", "#F59E0B", "#EF4444"],
      });
    }
  }, []);

  // Check if all checklist items are complete for a job
  const isJobComplete = (idx) => {
    const checklist = applications[idx]?.checklist || {};
    return (
      checklist.resume_ready &&
      checklist.cover_letter_ready &&
      checklist.applied_on_portal
    );
  };

  const allComplete =
    bestJobs.length > 0 && bestJobs.every((_, i) => isJobComplete(i));

  useEffect(() => {
    if (allComplete) {
      confetti({
        particleCount: 120,
        spread: 120,
        startVelocity: 30,
        origin: { y: 0.5 },
      });
    }
  }, [allComplete]);

  // Skeleton
  if (!bestJobs.length && state.status === "running") {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
        <div className="skeleton h-8 w-64" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-40" />
        ))}
      </div>
    );
  }

  // Empty
  if (!bestJobs.length) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="text-5xl">🚀</div>
        <h2 className="font-display text-xl font-bold text-slate-900">Not ready yet</h2>
        <p className="text-sm text-slate-500">Complete previous steps to reach the Apply Hub.</p>
      </motion.div>
    );
  }

  const handleDownloadAllResumes = () => {
    const a = document.createElement("a");
    a.href = `/api/download/resumes/${state.sessionId}/all`;
    a.download = "enhanced_resumes.zip";
    a.click();
  };

  const handleDownloadAllLetters = () => {
    const a = document.createElement("a");
    a.href = `/api/download/cover-letters/${state.sessionId}/all`;
    a.download = "cover_letters.zip";
    a.click();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto px-4 py-10 space-y-8"
    >
      {/* Header */}
      <div className="text-center space-y-2">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
        >
          <PartyPopper className="w-10 h-10 text-amber-500 mx-auto" aria-hidden="true" />
        </motion.div>
        <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
          Apply Hub
        </h2>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          Everything's ready — your enhanced resumes, cover letters, and
          application links are all in one place.
        </p>
      </div>

      {/* Bulk downloads */}
      <div className="flex flex-wrap justify-center gap-3">
        <Button variant="secondary" icon={Download} onClick={handleDownloadAllResumes}>
          All Resumes (ZIP)
        </Button>
        <Button variant="secondary" icon={Download} onClick={handleDownloadAllLetters}>
          All Cover Letters (ZIP)
        </Button>
      </div>

      {/* All-complete banner */}
      <AnimatePresence>
        {allComplete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-2xl p-4 text-center"
          >
            <p className="text-emerald-700 font-medium text-sm">
              🎉 All applications complete — you've got this!
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Application cards */}
      <div className="space-y-6">
        {bestJobs.map((job, i) => {
          const resume = resumes[i];
          const letter = letters[i];
          const app = applications[i] || {};
          const checklist = app.checklist || {};

          return (
            <motion.div
              key={`${job.title}-${i}`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <Card hover className="space-y-4">
                {/* Job header */}
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
                  <div className="flex-shrink-0 w-32">
                    <ScoreBar score={job.match_score || 0} />
                  </div>
                </div>

                {/* Checklist */}
                <div className="border border-slate-100 rounded-xl p-3 space-y-2 bg-slate-50/50">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500 mb-2">
                    Application Checklist
                  </p>
                  {[
                    {
                      key: "resume_ready",
                      label: "Enhanced resume downloaded",
                      icon: FileText,
                    },
                    {
                      key: "cover_letter_ready",
                      label: "Cover letter downloaded",
                      icon: Mail,
                    },
                    {
                      key: "applied_on_portal",
                      label: "Applied on portal",
                      icon: ExternalLink,
                    },
                  ].map((item) => (
                    <button
                      key={item.key}
                      onClick={() => toggleChecklist(i, item.key)}
                      className="flex items-center gap-2.5 w-full text-left group"
                    >
                      {checklist[item.key] ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-300 group-hover:text-slate-400 flex-shrink-0 transition-colors" />
                      )}
                      <item.icon
                        className={`w-4 h-4 ${
                          checklist[item.key]
                            ? "text-emerald-500"
                            : "text-slate-400"
                        }`}
                        aria-hidden="true"
                      />
                      <span
                        className={`text-sm ${
                          checklist[item.key]
                            ? "text-emerald-700 line-through"
                            : "text-slate-600"
                        }`}
                      >
                        {item.label}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Quick actions */}
                <div className="flex flex-wrap gap-2">
                  {resume && (
                    <a
                      href={`/api/download/resume/${state.sessionId}/${i}`}
                      download
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5" /> Resume
                    </a>
                  )}
                  {letter && (
                    <a
                      href={`/api/download/cover-letter/${state.sessionId}/${i}`}
                      download
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-violet-50 text-violet-700 hover:bg-violet-100 transition-colors"
                    >
                      <Mail className="w-3.5 h-3.5" /> Cover Letter
                    </a>
                  )}
                  {job.url && <ApplyButton url={job.url} portal={job.portal} />}
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Back */}
      <div className="flex justify-start pt-4">
        <button
          onClick={() => navigate("/cover-letters")}
          className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          ← Back to cover letters
        </button>
      </div>
    </motion.div>
  );
}
