"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronRight,
  Database,
  PlusCircle,
  Sun,
  Moon,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { useTheme } from "@/context/ThemeContext";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Executive Overview", subtitle: "Synthetic Student Engagement & Risk Dashboard" },
  "/generator": { title: "Data Generator Studio", subtitle: "Configure & Synthesize Longitudinal Academic Cohorts" },
  "/analytics": { title: "Student Analytics", subtitle: "Cohort Roster, Search, Multivariable Filters & History" },
  "/early-warning": { title: "Early Warning System (EWS)", subtitle: "Transparent Diagnostic Rules & MTSS Interventions" },
  "/ai-insights": { title: "Groq AI Pedagogical Insights", subtitle: "Deep AI Diagnosis & Multi-Tiered Intervention Planning" },
  "/curriculum": { title: "Institutions & Courses", subtitle: "Dynamic University Hierarchy, Departments & Course Catalogs" },
  "/datasets": { title: "Dataset Management", subtitle: "Saved Cohort Persistence, Comparison & Multi-Format Export" },
  "/settings": { title: "System & API Settings", subtitle: "Groq Engine Configuration & Database Telemetry" },
};

export function Header() {
  const pathname = usePathname();
  const { activeDataset, datasets, selectDataset } = useDataset();
  const { theme, toggleTheme } = useTheme();

  const currentMeta = PAGE_TITLES[pathname] || {
    title: "AttendSynth AI",
    subtitle: "Synthetic Student Engagement Platform",
  };

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800/80 bg-white/95 dark:bg-[#050811]/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20 transition-colors duration-200">
      {/* Left Section: Breadcrumb & Title Hierarchy (Spacious & Cleanly Aligned) */}
      <div className="flex flex-col justify-center min-w-0 pr-4">
        {/* Breadcrumb Trail */}
        <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-medium leading-none mb-1">
          <span>AttendSynth</span>
          <ChevronRight className="h-3 w-3 text-slate-400 dark:text-slate-600 shrink-0" />
          <span className="text-emerald-600 dark:text-emerald-400 font-semibold truncate">
            {currentMeta.title}
          </span>
          {activeDataset?.academic_year && (
            <span className="hidden sm:inline-flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 font-mono ml-1 shrink-0">
              <span>•</span>
              <span>{activeDataset.academic_year}</span>
            </span>
          )}
          {activeDataset?.institution_name && (
            <span className="hidden lg:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 ml-1 shrink-0">
              {activeDataset.institution_name}
            </span>
          )}
        </div>

        {/* Clean Page Title & Subtitle with generous spacing */}
        <div className="flex items-center gap-2 min-w-0">
          <h1 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white tracking-tight truncate">
            {currentMeta.title}
          </h1>
          <span className="hidden xl:inline text-xs font-normal text-slate-400 dark:text-slate-500 border-l border-slate-300 dark:border-slate-700/60 pl-2 truncate max-w-md">
            {currentMeta.subtitle}
          </span>
        </div>
      </div>

      {/* Right Controls: 1st Theme Toggle, then Cohort Selection, then New Cohort */}
      <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
        {/* 1. Theme Toggle (Dark / Light Theme) */}
        <button
          type="button"
          onClick={toggleTheme}
          title={theme === "dark" ? "Switch to Light Theme (White & Green)" : "Switch to Dark Theme (Black & Green)"}
          aria-label="Toggle Dark / Light Theme"
          className="flex items-center justify-center p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-[#0c1220] hover:bg-slate-200 dark:hover:bg-slate-800/80 text-slate-700 dark:text-slate-200 shadow-sm transition-all duration-150"
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4 text-emerald-400 hover:rotate-45 transition-transform" />
          ) : (
            <Moon className="h-4 w-4 text-emerald-600 hover:-rotate-12 transition-transform" />
          )}
        </button>

        {/* 2. Change Cohort Dropdown */}
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-[#0c1220] border border-slate-200 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 dark:text-slate-300 shadow-sm transition">
          <Database className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
          <span className="text-slate-500 dark:text-slate-400 text-[11px] font-medium hidden sm:inline">Active:</span>
          <select
            value={activeDataset?.id || ""}
            onChange={(e) => selectDataset(e.target.value)}
            aria-label="Change Active Academic Cohort"
            className="bg-transparent text-slate-900 dark:text-white font-medium text-xs focus:outline-none cursor-pointer max-w-[140px] sm:max-w-[200px] truncate"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                {d.name} ({d.num_students} STUs)
              </option>
            ))}
            {datasets.length === 0 && <option value="">No Datasets</option>}
          </select>
        </div>

        {/* 3. New Cohort Action Button */}
        <Link
          href="/generator"
          className="flex items-center gap-1.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white px-3 sm:px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm shadow-emerald-600/30 transition-all duration-150"
        >
          <PlusCircle className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">New Cohort</span>
        </Link>
      </div>
    </header>
  );
}
