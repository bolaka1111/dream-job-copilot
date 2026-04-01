import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  MapPin,
  Building2,
  DollarSign,
  Laptop,
  Factory,
  StickyNote,
} from "lucide-react";
import Card from "../components/common/Card";
import Input from "../components/common/Input";
import RadioGroup from "../components/common/RadioGroup";
import TextArea from "../components/common/TextArea";
import Button from "../components/common/Button";
import { usePipeline } from "../hooks/usePipeline";

const WORK_MODE_OPTIONS = [
  { value: "any", label: "No preference" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const COMPANY_SIZE_OPTIONS = [
  { value: "any", label: "Any size" },
  { value: "startup", label: "Startup (<50)" },
  { value: "mid", label: "Mid-size (50-500)" },
  { value: "enterprise", label: "Enterprise (500+)" },
];

export default function FeedbackPage() {
  const { state, submitFeedback } = usePipeline();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [form, setForm] = useState({
    industries: "",
    locations: "",
    workMode: "any",
    salaryMin: "",
    salaryMax: "",
    companySize: "any",
    notes: "",
  });

  const set = (key) => (e) =>
    setForm((prev) => ({ ...prev, [key]: e.target?.value ?? e }));

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await submitFeedback({
        preferred_industries: form.industries
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        preferred_locations: form.locations
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        work_mode: form.workMode,
        salary_range:
          form.salaryMin || form.salaryMax
            ? `${form.salaryMin || "0"}-${form.salaryMax || "any"}`
            : "",
        company_size: form.companySize,
        additional_notes: form.notes,
      });
      navigate("/best-jobs");
    } catch {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl mx-auto px-4 py-10 space-y-8"
    >
      <div>
        <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900">
          Your Preferences
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Tell us what matters to you — we'll refine our picks to match.
        </p>
      </div>

      {/* Industries */}
      <Card>
        <div className="flex items-center gap-2 mb-3">
          <Factory className="w-5 h-5 text-primary-500" aria-hidden="true" />
          <h3 className="font-semibold text-slate-700">Industries</h3>
        </div>
        <Input
          label="Preferred industries"
          placeholder="e.g. FinTech, HealthTech, EdTech"
          value={form.industries}
          onChange={set("industries")}
        />
        <p className="text-xs text-slate-400 mt-1">Comma-separated</p>
      </Card>

      {/* Location */}
      <Card>
        <div className="flex items-center gap-2 mb-3">
          <MapPin className="w-5 h-5 text-primary-500" aria-hidden="true" />
          <h3 className="font-semibold text-slate-700">Locations</h3>
        </div>
        <Input
          label="Preferred locations"
          placeholder="e.g. San Francisco, Berlin, Remote"
          value={form.locations}
          onChange={set("locations")}
        />
        <p className="text-xs text-slate-400 mt-1">Comma-separated</p>
      </Card>

      {/* Work mode */}
      <Card>
        <div className="flex items-center gap-2 mb-3">
          <Laptop className="w-5 h-5 text-primary-500" aria-hidden="true" />
          <h3 className="font-semibold text-slate-700">Work Mode</h3>
        </div>
        <RadioGroup
          name="workMode"
          options={WORK_MODE_OPTIONS}
          value={form.workMode}
          onChange={(v) => setForm((p) => ({ ...p, workMode: v }))}
        />
      </Card>

      {/* Salary */}
      <Card>
        <div className="flex items-center gap-2 mb-3">
          <DollarSign className="w-5 h-5 text-primary-500" aria-hidden="true" />
          <h3 className="font-semibold text-slate-700">Salary Range (Annual USD)</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Minimum"
            placeholder="e.g. 80000"
            type="number"
            value={form.salaryMin}
            onChange={set("salaryMin")}
          />
          <Input
            label="Maximum"
            placeholder="e.g. 150000"
            type="number"
            value={form.salaryMax}
            onChange={set("salaryMax")}
          />
        </div>
      </Card>

      {/* Company size */}
      <Card>
        <div className="flex items-center gap-2 mb-3">
          <Building2 className="w-5 h-5 text-primary-500" aria-hidden="true" />
          <h3 className="font-semibold text-slate-700">Company Size</h3>
        </div>
        <RadioGroup
          name="companySize"
          options={COMPANY_SIZE_OPTIONS}
          value={form.companySize}
          onChange={(v) => setForm((p) => ({ ...p, companySize: v }))}
        />
      </Card>

      {/* Notes */}
      <Card>
        <div className="flex items-center gap-2 mb-3">
          <StickyNote className="w-5 h-5 text-primary-500" aria-hidden="true" />
          <h3 className="font-semibold text-slate-700">Anything Else?</h3>
        </div>
        <TextArea
          label="Additional notes for our AI"
          placeholder="e.g. I prefer product-led companies, no agencies, ideally Series B+..."
          rows={4}
          value={form.notes}
          onChange={set("notes")}
        />
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={() => navigate("/recommendations")}
          className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          ← Back to picks
        </button>
        <Button
          icon={ArrowRight}
          loading={isSubmitting}
          onClick={handleSubmit}
        >
          {isSubmitting ? "Refining..." : "Refine My Picks"}
        </Button>
      </div>
    </motion.div>
  );
}
