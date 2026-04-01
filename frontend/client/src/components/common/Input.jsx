import React from "react";
import { cn } from "../../lib/utils";

export default function Input({
  label,
  id,
  className,
  error,
  icon: Icon,
  ...props
}) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-slate-700"
        >
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <Icon
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
            aria-hidden="true"
          />
        )}
        <input
          id={id}
          className={cn(
            "w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5",
            "text-sm text-slate-900 placeholder:text-slate-400",
            "transition-all duration-150",
            "hover:border-slate-300 focus:border-primary-400 focus:ring-2 focus:ring-primary-100",
            Icon && "pl-10",
            error && "border-rose-300 focus:border-rose-400 focus:ring-rose-100",
            className
          )}
          {...props}
        />
      </div>
      {error && (
        <p className="text-xs text-rose-500">{error}</p>
      )}
    </div>
  );
}
