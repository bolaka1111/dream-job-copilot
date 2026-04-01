import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Download,
  RefreshCw,
  FileText,
  Palette,
  AlignLeft,
} from "lucide-react";
import Card from "../components/common/Card";
import TabBar from "../components/common/TabBar";
import RadioGroup from "../components/common/RadioGroup";
import Button from "../components/common/Button";
import { usePipeline } from "../hooks/usePipeline";

const TONE_OPTIONS = [
  { value: "professional", label: "Professional" },
  { value: "friendly", label: "Friendly" },
  { value: "enthusiastic", label: "Enthusiastic" },
  { value: "concise", label: "Concise" },
];

const LENGTH_OPTIONS = [
  { value: "short", label: "Short (~200 words)" },
  { value: "medium", label: "Medium (~350 words)" },
  { value: "long", label: "Long (~500 words)" },
];

export default function CoverLettersPage() {
  const { state, regenerateCoverLetter } = usePipeline();
  const navigate = useNavigate();
  const letters = state.coverLetters || [];
  const [activeIdx, setActiveIdx] = useState(0);
  const [tone, setTone] = useState("professional");
  const [length, setLength] = useState("medium");
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Skeleton
  if (!letters.length && state.status === "running") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        <div className="skeleton h-8 w-72" />
        <div className="skeleton h-80" />
      </div>
    );
  }

  // Empty
  if (!letters.length) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="text-5xl">✉️</div>
        <h2 className="font-display text-xl font-bold text-slate-900">No cover letters yet</h2>
        <p className="text-sm text-slate-500">Complete earlier stages first.</p>
      </motion.div>
    );
  }

  const active = letters[activeIdx] || letters[0];
  const tabs = letters.map((l, i) => ({
    key: String(i),
    label: l.target_role || l.company || `Letter ${i + 1}`,
  }));

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      await regenerateCoverLetter(activeIdx, { tone, length });
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleDownloadOne = () => {
    const a = document.createElement("a");
    a.href = `/api/download/cover-letter/${state.sessionId}/${activeIdx}`;
    a.download = `cover_letter_${activeIdx + 1}.txt`;
    a.click();
  };

  const handleDownloadAll = () => {
    const a = document.createElement("a");
    a.href = `/api/download/cover-letters/${state.sessionId}/all`;
    a.download = "cover_letters.zip";
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
            Cover Letters
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            One for each role — tweak tone and length, regenerate as needed
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" icon={Download} onClick={handleDownloadOne}>
            This Letter
          </Button>
          <Button variant="secondary" size="sm" icon={Download} onClick={handleDownloadAll}>
            All Letters
          </Button>
        </div>
      </div>

      {/* Tabs */}
      {letters.length > 1 && (
        <TabBar
          tabs={tabs}
          activeKey={String(activeIdx)}
          onChange={(key) => setActiveIdx(Number(key))}
        />
      )}

      {/* Controls */}
      <div className="grid sm:grid-cols-2 gap-4">
        <Card className="space-y-3">
          <div className="flex items-center gap-2">
            <Palette className="w-4 h-4 text-primary-500" aria-hidden="true" />
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Tone</span>
          </div>
          <RadioGroup
            name="tone"
            options={TONE_OPTIONS}
            value={tone}
            onChange={setTone}
          />
        </Card>
        <Card className="space-y-3">
          <div className="flex items-center gap-2">
            <AlignLeft className="w-4 h-4 text-primary-500" aria-hidden="true" />
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Length</span>
          </div>
          <RadioGroup
            name="length"
            options={LENGTH_OPTIONS}
            value={length}
            onChange={setLength}
          />
        </Card>
      </div>

      <div className="flex justify-center">
        <Button
          variant="secondary"
          icon={RefreshCw}
          loading={isRegenerating}
          onClick={handleRegenerate}
        >
          {isRegenerating ? "Regenerating..." : "Regenerate This Letter"}
        </Button>
      </div>

      {/* Letter preview — typewriter-style entrance per guardrails §5 */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${activeIdx}-${active.content?.length}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25 }}
        >
          <Card className="space-y-3">
            {active.target_role && (
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary-500" aria-hidden="true" />
                <span className="text-sm font-medium text-slate-600">
                  For{" "}
                  <span className="text-primary-700 font-semibold">
                    {active.target_role}
                  </span>
                  {active.company && ` at ${active.company}`}
                </span>
              </div>
            )}
            <div className="prose prose-slate prose-sm max-w-none whitespace-pre-wrap text-slate-700 leading-relaxed border border-slate-100 rounded-xl p-4 bg-slate-50/50">
              {active.content || "No content available."}
            </div>
          </Card>
        </motion.div>
      </AnimatePresence>

      {/* Continue */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={() => navigate("/enhanced-resumes")}
          className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          ← Back to resumes
        </button>
        <Button
          icon={ArrowRight}
          onClick={() => navigate("/apply")}
        >
          Go to Apply Hub
        </Button>
      </div>
    </motion.div>
  );
}
