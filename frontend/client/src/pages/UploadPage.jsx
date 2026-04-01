import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Rocket, Sparkles } from "lucide-react";
import confetti from "canvas-confetti";
import DropZone from "../components/DropZone";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import RadioGroup from "../components/common/RadioGroup";
import { usePipeline } from "../hooks/usePipeline";

const SEARCH_SCOPE_OPTIONS = [
  { value: "global", label: "Anywhere in the world" },
  { value: "regional", label: "Specific regions" },
  { value: "remote", label: "Remote only" },
  { value: "relocation", label: "Open to relocation" },
];

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [dreamRole, setDreamRole] = useState("");
  const [searchScope, setSearchScope] = useState("global");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { state, startPipeline } = usePipeline();
  const navigate = useNavigate();

  const handleFileSelect = (f) => {
    setFile(f);
    // Confetti burst on successful upload — guardrails §5
    confetti({
      particleCount: 40,
      spread: 50,
      origin: { y: 0.6 },
      colors: ["#10B981", "#6366F1", "#F59E0B"],
    });
  };

  // Navigate to resume-review once the profile data arrives via SSE
  useEffect(() => {
    if (isSubmitting && state.resumeProfile) {
      setIsSubmitting(false);
      navigate("/resume-review");
    }
  }, [state.resumeProfile, isSubmitting, navigate]);

  // Navigate even if pipeline_complete fires before profile (fallback)
  useEffect(() => {
    if (isSubmitting && state.status === "completed") {
      setIsSubmitting(false);
      navigate("/resume-review");
    }
  }, [state.status, isSubmitting, navigate]);

  // If error, stop the spinner and show the real error message
  useEffect(() => {
    if (isSubmitting && state.status === "error") {
      setIsSubmitting(false);
      // The last log message often has the real error from the pipeline
      const lastErr = state.errors?.[state.errors.length - 1] || "";
      const lastLog = state.logMessages?.[state.logMessages.length - 1] || "";
      const detail = lastErr || lastLog;
      if (detail && detail.includes("quota")) {
        toast.error("OpenAI API quota exceeded — please check your billing at platform.openai.com");
      } else if (detail && detail.includes("api_key")) {
        toast.error("Invalid OpenAI API key — please check your .env file");
      }
    }
  }, [state.status, isSubmitting, state.errors, state.logMessages]);

  const handleStart = async () => {
    if (!file) return;
    setIsSubmitting(true);
    try {
      await startPipeline(file, { dreamRole, searchScope });
      // Don't navigate here — wait for SSE data in the effects above
    } catch {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="max-w-2xl mx-auto px-4 py-12 space-y-8"
    >
      {/* Hero */}
      <div className="text-center space-y-3">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
          className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg mb-2"
        >
          <Rocket className="w-8 h-8 text-white" />
        </motion.div>
        <h1 className="font-display text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
          Dream Job Copilot
        </h1>
        <p className="text-base text-slate-500 leading-relaxed max-w-md mx-auto">
          Find the job you actually want, anywhere in the world. Upload your
          resume and we'll handle the rest.
        </p>
      </div>

      {/* Drop zone */}
      <DropZone
        onFileSelect={handleFileSelect}
        file={file}
        onRemove={() => setFile(null)}
      />

      {/* Search scope */}
      <RadioGroup
        label="Where do you want to search?"
        name="searchScope"
        options={SEARCH_SCOPE_OPTIONS}
        value={searchScope}
        onChange={setSearchScope}
      />

      {/* Dream role input */}
      <Input
        label="What kind of roles are you dreaming of?"
        id="dreamRole"
        placeholder="e.g. Head of Engineering, Staff Engineer at FAANG..."
        value={dreamRole}
        onChange={(e) => setDreamRole(e.target.value)}
        icon={Sparkles}
      />
      <p className="text-xs text-slate-400 -mt-6 ml-1">
        Optional — helps us find aspirational roles too
      </p>

      {/* CTA */}
      <div className="pt-4">
        <Button
          size="lg"
          className="w-full"
          disabled={!file}
          loading={isSubmitting}
          icon={Rocket}
          onClick={handleStart}
        >
          {isSubmitting ? "Analysing your resume..." : "Find My Dream Job"}
        </Button>
      </div>
    </motion.div>
  );
}
