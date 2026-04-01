import React from "react";
import { cn } from "../../lib/utils";

const colorMap = {
  default: "bg-slate-100 text-slate-700",
  primary: "bg-primary-100 text-primary-700",
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  rose: "bg-rose-100 text-rose-700",
  violet: "bg-violet-100 text-violet-700",
  blue: "bg-blue-100 text-blue-700",
};

export default function Badge({ children, color = "default", className, ...props }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full",
        "text-xs font-medium uppercase tracking-wide",
        "transition-colors duration-150",
        colorMap[color] || colorMap.default,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
