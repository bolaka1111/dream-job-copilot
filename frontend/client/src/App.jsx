import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import Header from "./components/Header";
import ProgressStepper from "./components/ProgressStepper";
import LoadingOverlay from "./components/LoadingOverlay";
import { usePipeline } from "./hooks/usePipeline";
import { useSSE } from "./hooks/useSSE";

// Pages
import UploadPage from "./pages/UploadPage";
import ResumeReviewPage from "./pages/ResumeReviewPage";
import JobSearchPage from "./pages/JobSearchPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import FeedbackPage from "./pages/FeedbackPage";
import BestJobsPage from "./pages/BestJobsPage";
import EnhancedResumesPage from "./pages/EnhancedResumesPage";
import CoverLettersPage from "./pages/CoverLettersPage";
import ApplyHubPage from "./pages/ApplyHubPage";

/**
 * Maps route paths → stepper step index (0-based).
 * Used by ProgressStepper to highlight the current step.
 */
const ROUTE_TO_STEP = {
  "/": 1,
  "/resume-review": 2,
  "/job-search": 3,
  "/recommendations": 4,
  "/preferences": 5,
  "/best-jobs": 7,
  "/enhanced-resumes": 8,
  "/cover-letters": 9,
  "/apply": 10,
};

export default function App() {
  const { state } = usePipeline();
  const location = useLocation();

  // Connect SSE when sessionId is available
  useSSE();

  // Derive current step from pathname
  const routeStep = ROUTE_TO_STEP[location.pathname] ?? 1;
  const currentStage = Math.max(routeStep, state.currentStage || 0);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Toast notifications — guardrails compliant positioning */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            borderRadius: "1rem",
            fontSize: "0.875rem",
            fontFamily: "Inter, sans-serif",
          },
        }}
      />

      {/* Sticky header */}
      <Header />

      {/* Progress stepper — hidden on landing page */}
      {state.sessionId && (
        <div className="border-b border-slate-100 bg-white/80 backdrop-blur-sm sticky top-14 z-30">
          <div className="max-w-5xl mx-auto px-4 py-3">
            <ProgressStepper currentStage={currentStage} />
          </div>
        </div>
      )}

      {/* Page content */}
      <main className="flex-1 pb-16">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/resume-review" element={<ResumeReviewPage />} />
          <Route path="/job-search" element={<JobSearchPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/preferences" element={<FeedbackPage />} />
          <Route path="/best-jobs" element={<BestJobsPage />} />
          <Route path="/enhanced-resumes" element={<EnhancedResumesPage />} />
          <Route path="/cover-letters" element={<CoverLettersPage />} />
          <Route path="/apply" element={<ApplyHubPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Loading overlay for background processing */}
      <LoadingOverlay />
    </div>
  );
}
