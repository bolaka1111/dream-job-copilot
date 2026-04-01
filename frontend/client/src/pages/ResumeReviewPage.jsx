import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, User, Briefcase, Clock, GraduationCap, AlertTriangle } from "lucide-react";
import Card from "../components/common/Card";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import { usePipeline } from "../hooks/usePipeline";

const SKILL_COLORS = ["primary", "emerald", "amber", "violet", "blue", "rose"];

export default function ResumeReviewPage() {
  const { state } = usePipeline();
  const navigate = useNavigate();
  const profile = state.resumeProfile;

  // Skeleton loader — guardrails §3
  if (!profile) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
        <div className="skeleton h-8 w-64" />
        <div className="grid md:grid-cols-2 gap-6">
          <div className="skeleton h-72" />
          <div className="skeleton h-72" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto px-4 py-10 space-y-6"
    >
      <div>
        <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900">
          Your Resume Profile
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Here's what we found — looking good!
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Profile Card */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="h-full space-y-5">
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 rounded-2xl bg-primary-100 flex items-center justify-center flex-shrink-0">
                <User className="w-6 h-6 text-primary-600" aria-hidden="true" />
              </div>
              <div>
                <h3 className="font-display text-lg font-bold text-slate-900">
                  {profile.current_role || "Professional"}
                </h3>
              </div>
            </div>

            {/* Experience */}
            {profile.experience_years > 0 && (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Clock className="w-4 h-4 text-slate-400" aria-hidden="true" />
                <span>{profile.experience_years} years of experience</span>
              </div>
            )}

            {/* Education */}
            {profile.education?.length > 0 && (
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                  <GraduationCap className="w-3.5 h-3.5" aria-hidden="true" />
                  Education
                </div>
                {profile.education.map((edu, i) => (
                  <p key={i} className="text-sm text-slate-600 ml-5">{edu}</p>
                ))}
              </div>
            )}

            {/* Skills */}
            {profile.skills?.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Core Skills
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {profile.skills.map((skill, i) => (
                    <Badge
                      key={skill}
                      color={SKILL_COLORS[i % SKILL_COLORS.length]}
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Target roles */}
            {profile.target_roles?.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Target Roles
                </p>
                <ul className="space-y-1">
                  {profile.target_roles.map((role, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
                      <Briefcase className="w-3.5 h-3.5 text-primary-400" aria-hidden="true" />
                      {role}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        </motion.div>

        {/* AI Review Panel */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="h-full space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-indigo-100 flex items-center justify-center">
                <span className="text-base">🤖</span>
              </div>
              <h3 className="text-base font-semibold text-slate-700">
                AI Review
              </h3>
            </div>

            {profile.review ? (
              <div className="ai-callout">{profile.review}</div>
            ) : (
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <AlertTriangle className="w-4 h-4" />
                No AI review available
              </div>
            )}
          </Card>
        </motion.div>
      </div>

      {/* Continue */}
      <div className="flex justify-end pt-4">
        <Button
          icon={ArrowRight}
          onClick={() => navigate("/job-search")}
          disabled={!state.jobResults?.length}
        >
          Continue to Job Search
        </Button>
      </div>
    </motion.div>
  );
}
