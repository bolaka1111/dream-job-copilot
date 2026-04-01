import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Download,
  FileText,
  ChevronDown,
  ChevronUp,
  Plus,
  Minus,
} from "lucide-react";
import Card from "../components/common/Card";
import Badge from "../components/common/Badge";
import TabBar from "../components/common/TabBar";
import Button from "../components/common/Button";
import { usePipeline } from "../hooks/usePipeline";

export default function EnhancedResumesPage() {
  const { state } = usePipeline();
  const navigate = useNavigate();
  const resumes = state.enhancedResumes || [];
  const [activeIdx, setActiveIdx] = useState(0);
  const [showChanges, setShowChanges] = useState(false);

  // Skeleton
  if (!resumes.length && state.status === "running") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        <div className="skeleton h-8 w-72" />
        <div className="skeleton h-96" />
      </div>
    );
  }

  // Empty
  if (!resumes.length) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="text-5xl">📝</div>
        <h2 className="font-display text-xl font-bold text-slate-900">No enhanced resumes yet</h2>
        <p className="text-sm text-slate-500">
          Complete the review stage first.
        </p>
      </motion.div>
    );
  }

  const active = resumes[activeIdx] || resumes[0];
  const tabs = resumes.map((r, i) => ({
    key: String(i),
    label: r.target_role || r.company || `Resume ${i + 1}`,
  }));

  const handleDownloadOne = () => {
    const a = document.createElement("a");
    a.href = `/api/download/resume/${state.sessionId}/${activeIdx}`;
    a.download = `resume_${activeIdx + 1}.txt`;
    a.click();
  };

  const handleDownloadAll = () => {
    const a = document.createElement("a");
    a.href = `/api/download/resumes/${state.sessionId}/all`;
    a.download = "enhanced_resumes.zip";
    a.click();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto px-4 py-10 space-y-6"
    >
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900">
            Enhanced Resumes
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Tailored for each top role — ready to send
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" icon={Download} onClick={handleDownloadOne}>
            This Resume
          </Button>
          <Button variant="secondary" size="sm" icon={Download} onClick={handleDownloadAll}>
            Download All
          </Button>
        </div>
      </div>

      {/* Tab bar */}
      {resumes.length > 1 && (
        <TabBar
          tabs={tabs}
          activeKey={String(activeIdx)}
          onChange={(key) => setActiveIdx(Number(key))}
        />
      )}

      {/* Resume preview */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeIdx}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          <Card className="space-y-4">
            {/* Target role badge */}
            {active.target_role && (
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary-500" aria-hidden="true" />
                <span className="text-sm font-medium text-slate-600">
                  Tailored for{" "}
                  <span className="text-primary-700 font-semibold">
                    {active.target_role}
                  </span>
                  {active.company && ` at ${active.company}`}
                </span>
              </div>
            )}

            {/* Resume content */}
            <div className="prose prose-slate prose-sm max-w-none whitespace-pre-wrap text-slate-700 leading-relaxed border border-slate-100 rounded-xl p-4 bg-slate-50/50">
              {active.content || active.enhanced_content || "No content available."}
            </div>

            {/* Changes summary toggle */}
            {active.changes?.length > 0 && (
              <div>
                <button
                  onClick={() => setShowChanges(!showChanges)}
                  className="flex items-center gap-1.5 text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
                >
                  {showChanges ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                  {showChanges ? "Hide" : "Show"} what changed (
                  {active.changes.length})
                </button>
                <AnimatePresence>
                  {showChanges && (
                    <motion.ul
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-2 space-y-1.5 overflow-hidden"
                    >
                      {active.changes.map((change, ci) => (
                        <li
                          key={ci}
                          className="flex items-start gap-2 text-xs text-slate-600"
                        >
                          {change.type === "added" ? (
                            <Plus className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                          ) : (
                            <Minus className="w-3.5 h-3.5 text-rose-500 flex-shrink-0 mt-0.5" />
                          )}
                          <span>{change.description || change}</span>
                        </li>
                      ))}
                    </motion.ul>
                  )}
                </AnimatePresence>
              </div>
            )}
          </Card>
        </motion.div>
      </AnimatePresence>

      {/* Continue */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={() => navigate("/best-jobs")}
          className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          ← Back to best matches
        </button>
        <Button
          icon={ArrowRight}
          onClick={() => navigate("/cover-letters")}
          disabled={!state.coverLetters?.length}
        >
          View Cover Letters
        </Button>
      </div>
    </motion.div>
  );
}
