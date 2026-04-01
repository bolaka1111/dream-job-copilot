import React from "react";
import { cn } from "../../lib/utils";

export default function TextArea({ label, id, className, error, ...props }) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <textarea
        id={id}
        rows={4}
        className={cn(
          "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3",
          "text-sm text-slate-900 placeholder:text-slate-400",
          "transition-all duration-150 resize-y",
          "hover:border-slate-300 focus:border-primary-400 focus:ring-2 focus:ring-primary-100",
          error && "border-rose-300 focus:border-rose-400 focus:ring-rose-100",
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-rose-500">{error}</p>}
    </div>
  );
}
