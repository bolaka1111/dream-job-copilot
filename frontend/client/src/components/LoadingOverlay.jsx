import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2 } from "lucide-react";
import { usePipelineContext } from "../context/PipelineContext";

export default function LoadingOverlay() {
  const { state } = usePipelineContext();
  // Only show overlay when pipeline is actively running AND no page data has arrived yet.
  // Once any real data lands (resumeProfile, jobResults, etc.) pages show their own content.
  const hasAnyData = !!(state.resumeProfile || state.jobResults?.length || state.bestJobs?.length || state.enhancedResumes?.length);
  const isLoading = state.status === "running" && !hasAnyData;
  const lastMsg = state.logMessages[state.logMessages.length - 1] || "";

  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/20 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 text-center space-y-4"
          >
            <div className="flex justify-center">
              <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
            </div>
            <div>
              <h3 className="font-display text-lg font-bold text-slate-900">
                Working on it...
              </h3>
              {/* Typewriter-fade message — guardrails §2 */}
              <AnimatePresence mode="wait">
                <motion.p
                  key={lastMsg}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="text-sm text-slate-500 mt-2"
                >
                  {lastMsg || "We're getting everything ready for you..."}
                </motion.p>
              </AnimatePresence>
            </div>

            {/* Live log strip — guardrails §3 */}
            {state.logMessages.length > 1 && (
              <div className="mt-4 max-h-24 overflow-y-auto bg-slate-50 rounded-xl p-3 text-left">
                {state.logMessages.slice(-5).map((msg, i) => (
                  <motion.p
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: i === state.logMessages.slice(-5).length - 1 ? 1 : 0.5 }}
                    className="text-[11px] text-slate-500 font-mono truncate"
                  >
                    {msg}
                  </motion.p>
                ))}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
