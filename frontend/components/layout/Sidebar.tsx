"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Sliders,
  Users,
  AlertTriangle,
  Bot,
  Database,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  GraduationCap,
  Building2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDataset } from "@/context/DatasetContext";

const NAV_ITEMS = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Data Generator", href: "/generator", icon: Sliders },
  { name: "Institutions & Courses", href: "/curriculum", icon: Building2 },
  { name: "Student Analytics", href: "/analytics", icon: Users },
  { name: "Early Warning", href: "/early-warning", icon: AlertTriangle },
  { name: "AI Insights", href: "/ai-insights", icon: Bot },
  { name: "Dataset Management", href: "/datasets", icon: Database },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { activeDataset } = useDataset();

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#050811] transition-all duration-300 ease-in-out select-none z-30 shrink-0",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header: Centered when collapsed, spacious when expanded */}
      <div
        className={cn(
          "flex h-16 items-center border-b border-slate-200 dark:border-slate-800/80 transition-all",
          collapsed ? "justify-center px-0" : "px-4"
        )}
      >
        <Link
          href="/"
          className={cn(
            "flex items-center gap-3",
            collapsed ? "justify-center w-full" : "overflow-hidden"
          )}
          title="AttendSynth AI"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 shadow-md shadow-emerald-500/20 text-white">
            <GraduationCap className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
                AttendSynth{" "}
                <span className="text-xs font-mono font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-1 py-0.5 rounded">
                  AI
                </span>
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                Student Engagement
              </span>
            </div>
          )}
        </Link>
      </div>

      {/* Navigation Items: Large spacing and comfortable touch targets when collapsed */}
      <nav
        className={cn(
          "flex-1 overflow-y-auto transition-all",
          collapsed ? "py-5 px-2 space-y-3.5" : "p-2.5 space-y-1"
        )}
      >
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center transition-all duration-150 relative",
                collapsed
                  ? "w-11 h-11 mx-auto justify-center rounded-xl"
                  : "gap-3 rounded-lg px-3 py-2 text-xs font-medium",
                isActive
                  ? "bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 font-semibold shadow-sm shadow-emerald-500/10"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200 border border-transparent"
              )}
              title={item.name}
            >
              <Icon
                className={cn(
                  "shrink-0 transition-colors",
                  collapsed ? "h-5 w-5" : "h-4 w-4",
                  isActive
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-slate-500 dark:text-slate-400 group-hover:text-slate-800 dark:group-hover:text-slate-200"
                )}
              />
              {!collapsed && <span className="truncate">{item.name}</span>}
              {!collapsed && isActive && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
              )}
              {collapsed && isActive && (
                <div className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Cohort Pill & FERPA info */}
      {collapsed ? (
        <div className="py-2.5 flex justify-center" title="100% Synthetic (FERPA Safe)">
          <div className="p-2 rounded-xl bg-slate-50 dark:bg-[#090e17] border border-slate-200 dark:border-slate-800/80 text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="h-4 w-4" />
          </div>
        </div>
      ) : (
        <div className="p-3 mx-2.5 mb-2 rounded-lg bg-slate-50 dark:bg-[#090e17] border border-slate-200 dark:border-slate-800/80 text-[11px]">
          <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 mb-1">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
            <span className="font-semibold text-slate-800 dark:text-slate-200">100% Synthetic</span>
          </div>
          <div className="text-slate-600 dark:text-slate-400 truncate">
            {activeDataset ? activeDataset.name : "No Active Cohort"}
          </div>
          <div className="text-slate-400 dark:text-slate-500 text-[10px] mt-0.5 font-mono">
            {activeDataset ? `${activeDataset.num_students} STUs • ${activeDataset.num_weeks} Wks` : ""}
          </div>
        </div>
      )}

      {/* Collapse Toggle */}
      <div
        className={cn(
          "p-2 border-t border-slate-200 dark:border-slate-800/80 flex items-center transition-all",
          collapsed ? "justify-center" : "justify-between"
        )}
      >
        {!collapsed && (
          <span className="text-[11px] text-slate-400 dark:text-slate-500 pl-2 font-mono">
            v2.0 • SaaS Grade
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "rounded-xl text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition flex items-center justify-center",
            collapsed ? "w-11 h-11" : "p-1.5 ml-auto"
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  );
}
