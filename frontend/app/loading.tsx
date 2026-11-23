import React from "react";
import { GraduationCap } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] w-full px-4 select-none">
      <div className="flex flex-col items-center space-y-4">
        {/* Pulsing Emerald Logo */}
        <div className="relative flex items-center justify-center">
          <div className="absolute h-16 w-16 rounded-2xl bg-emerald-500/20 dark:bg-emerald-500/25 animate-ping opacity-75" />
          <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/20">
            <GraduationCap className="h-7 w-7 animate-pulse" />
          </div>
        </div>

        {/* Text Details */}
        <div className="flex flex-col items-center space-y-1 text-center">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-800 dark:text-white tracking-tight">
              AttendSynth
            </span>
            <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
              AI
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Loading module workspace & telemetry...
          </p>
        </div>

        {/* Sleek Spinner / Bar */}
        <div className="flex items-center gap-1.5 pt-1">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:-0.3s]" />
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:-0.15s]" />
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-bounce" />
        </div>
      </div>
    </div>
  );
}
