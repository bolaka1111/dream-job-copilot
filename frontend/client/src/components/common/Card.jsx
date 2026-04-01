import React from "react";
import { cn } from "../../lib/utils";

export default function Card({ children, className, hover = false, ...props }) {
  return (
    <div
      className={cn(
        "bg-white rounded-2xl p-6 shadow-sm border border-slate-100",
        "transition-all duration-200 ease-out",
        hover && "hover:shadow-xl hover:-translate-y-0.5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
