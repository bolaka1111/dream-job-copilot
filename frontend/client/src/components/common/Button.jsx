import React from "react";
import { cn } from "../../lib/utils";

const variants = {
  primary:
    "bg-primary-500 text-white hover:bg-primary-600 shadow-sm hover:shadow-xl active:scale-[0.98]",
  secondary:
    "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-sm hover:shadow-md",
  ghost:
    "bg-transparent text-slate-600 hover:bg-slate-100",
  success:
    "bg-emerald-500 text-white hover:bg-emerald-600 shadow-sm hover:shadow-xl",
  danger:
    "bg-rose-500 text-white hover:bg-rose-600",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-5 py-2.5 text-sm",
  lg: "px-7 py-3.5 text-base min-h-[48px]",
};

export default React.memo(function Button({
  children,
  variant = "primary",
  size = "md",
  className,
  disabled,
  loading,
  icon: Icon,
  ...props
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 font-semibold rounded-full",
        "transition-all duration-200 ease-out",
        "hover:scale-105 focus-visible:ring-2 focus-visible:ring-primary-500",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg
          className="animate-spin h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : Icon ? (
        <Icon className="w-4 h-4" aria-hidden="true" />
      ) : null}
      {children}
    </button>
  );
});
