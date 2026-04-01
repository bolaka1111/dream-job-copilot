import React from "react";
import { cn } from "../../lib/utils";

export default function TabBar({ tabs, activeTab, onChange, className }) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 p-1 bg-slate-100 rounded-full",
        className
      )}
      role="tablist"
    >
      {tabs.map((tab) => (
        <button
          key={tab.value}
          role="tab"
          aria-selected={activeTab === tab.value}
          onClick={() => onChange(tab.value)}
          className={cn(
            "px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200",
            activeTab === tab.value
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
