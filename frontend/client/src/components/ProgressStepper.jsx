import React from "react";
import { cn } from "../lib/utils";
import { Check } from "lucide-react";

const STEPS = [
  { num: 1, label: "Upload" },
  { num: 2, label: "Profile" },
  { num: 3, label: "Search" },
  { num: 4, label: "Picks" },
  { num: 5, label: "Prefs" },
  { num: 6, label: "Reviews" },
  { num: 7, label: "Best" },
  { num: 8, label: "Resumes" },
  { num: 9, label: "Letters" },
  { num: 10, label: "Apply" },
];

export default function ProgressStepper({ currentStage, onStepClick }) {
  return (
    <nav
      aria-label="Pipeline progress"
      className="w-full bg-white border-b border-slate-100 py-3 px-4 overflow-x-auto"
    >
      <div className="max-w-5xl mx-auto">
        {/* Desktop stepper */}
        <ol className="hidden sm:flex items-center justify-between gap-1">
          {STEPS.map((step, i) => {
            const isCompleted = currentStage > step.num;
            const isActive = currentStage === step.num;
            const isPending = currentStage < step.num;

            return (
              <li
                key={step.num}
                className="flex items-center gap-1.5 flex-1 last:flex-none"
              >
                <button
                  onClick={() => isCompleted && onStepClick?.(step.num)}
                  disabled={!isCompleted}
                  className={cn(
                    "flex flex-col items-center gap-1 group",
                    isCompleted && "cursor-pointer"
                  )}
                  aria-label={`Step ${step.num}: ${step.label}${isCompleted ? " (completed)" : isActive ? " (current)" : ""}`}
                >
                  <span
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold",
                      "transition-all duration-300",
                      isCompleted &&
                        "bg-emerald-500 text-white shadow-sm group-hover:shadow-md group-hover:scale-110",
                      isActive &&
                        "bg-primary-500 text-white shadow-md animate-pulse-ring",
                      isPending &&
                        "bg-slate-100 text-slate-400 border-2 border-slate-200"
                    )}
                  >
                    {isCompleted ? (
                      <Check className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      step.num
                    )}
                  </span>
                  <span
                    className={cn(
                      "text-[10px] font-medium tracking-wide",
                      isCompleted && "text-emerald-600",
                      isActive && "text-primary-600",
                      isPending && "text-slate-400"
                    )}
                  >
                    {step.label}
                  </span>
                </button>

                {/* Connector line */}
                {i < STEPS.length - 1 && (
                  <div
                    className={cn(
                      "flex-1 h-0.5 rounded-full mx-1 transition-colors duration-500",
                      currentStage > step.num + 1
                        ? "bg-emerald-400"
                        : currentStage > step.num
                          ? "bg-gradient-to-r from-emerald-400 to-slate-200"
                          : "bg-slate-200"
                    )}
                  />
                )}
              </li>
            );
          })}
        </ol>

        {/* Mobile stepper — collapsed per guardrails §7 */}
        <div className="sm:hidden flex items-center justify-center gap-3">
          <span className="text-xs font-medium text-slate-500">
            Step {currentStage} of 10
          </span>
          <div className="flex gap-1">
            {STEPS.map((step) => (
              <span
                key={step.num}
                className={cn(
                  "w-2 h-2 rounded-full transition-all duration-300",
                  currentStage > step.num && "bg-emerald-500",
                  currentStage === step.num && "bg-primary-500 w-6",
                  currentStage < step.num && "bg-slate-200"
                )}
              />
            ))}
          </div>
          <span className="text-xs font-semibold text-primary-600">
            {STEPS.find((s) => s.num === currentStage)?.label || ""}
          </span>
        </div>
      </div>
    </nav>
  );
}
