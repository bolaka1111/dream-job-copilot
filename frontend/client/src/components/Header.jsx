import React from "react";
import { Rocket } from "lucide-react";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-sm">
            <Rocket className="w-5 h-5 text-white" aria-hidden="true" />
          </div>
          <h1 className="font-display text-lg font-bold tracking-tight text-slate-900">
            Dream Job Copilot
          </h1>
        </div>
      </div>
    </header>
  );
}
