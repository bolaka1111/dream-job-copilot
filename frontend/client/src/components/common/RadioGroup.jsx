import React from "react";
import { cn } from "../../lib/utils";

export default function RadioGroup({ label, name, options, value, onChange, className }) {
  return (
    <fieldset className={cn("space-y-2", className)}>
      {label && (
        <legend className="block text-sm font-medium text-slate-700 mb-2">
          {label}
        </legend>
      )}
      <div className="flex flex-wrap gap-3">
        {options.map((opt) => (
          <label
            key={opt.value}
            className={cn(
              "inline-flex items-center gap-2 px-4 py-2 rounded-full cursor-pointer",
              "border text-sm font-medium transition-all duration-200",
              "hover:scale-105",
              value === opt.value
                ? "border-primary-500 bg-primary-50 text-primary-700 shadow-sm"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
            )}
          >
            <input
              type="radio"
              name={name}
              value={opt.value}
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
              className="sr-only"
            />
            <span
              className={cn(
                "w-4 h-4 rounded-full border-2 flex items-center justify-center",
                "transition-colors",
                value === opt.value
                  ? "border-primary-500"
                  : "border-slate-300"
              )}
            >
              {value === opt.value && (
                <span className="w-2 h-2 rounded-full bg-primary-500" />
              )}
            </span>
            {opt.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
