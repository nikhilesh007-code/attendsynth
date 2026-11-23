"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  CalendarCheck2,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Sliders,
  Bot,
  Database,
  Layers,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { api } from "@/lib/api";
import { CohortKPIs, CohortDistributions, WeeklyTrend, EarlyWarningFlaggedStudent } from "@/types";
import { KPICard } from "@/components/dashboard/KPICard";
import { WeeklyTrendChart } from "@/components/charts/WeeklyTrendChart";
import { DonutDistributionChart } from "@/components/charts/DonutDistributionChart";
import { DistributionBarChart } from "@/components/charts/DistributionBarChart";
import { StudentDrawer } from "@/components/students/StudentDrawer";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";

export default function DashboardPage() {
  const { activeDataset, datasets, scopes } = useDataset();

  const [kpis, setKpis] = useState<CohortKPIs | null>(null);
  const [distributions, setDistributions] = useState<CohortDistributions | null>(null);
  const [trends, setTrends] = useState<WeeklyTrend[]>([]);
  const [flaggedStudents, setFlaggedStudents] = useState<EarlyWarningFlaggedStudent[]>([]);
  const [aiSummary, setAiSummary] = useState<string>("");
  const [aiIsFallback, setAiIsFallback] = useState<boolean>(false);
  const [aiStatus, setAiStatus] = useState<string>("");
  const [aiLoading, setAiLoading] = useState<boolean>(false);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);

  useEffect(() => {
    if (!activeDataset) return;

    // Fetch dashboard data
    api.getKPIs(activeDataset.id).then(setKpis).catch(console.error);
    api.getDistributions(activeDataset.id).then(setDistributions).catch(console.error);
    api.getWeeklyTrends(activeDataset.id).then(setTrends).catch(console.error);
    api
      .getEarlyWarningSummary(activeDataset.id)
      .then((ews) => setFlaggedStudents(ews.flagged_students.slice(0, 8)))
      .catch(console.error);

    // Fetch brief executive summary
    setAiLoading(true);
    api
      .getExecutiveSummary(activeDataset.id)
      .then((res) => {
        setAiSummary(res.response);
        setAiIsFallback(res.is_fallback);
        setAiStatus(res.status);
      })
      .catch((err) => {
        console.error("Executive summary error:", err);
        setAiSummary("Local synthetic heuristics active. Groq AI diagnostic ready on demand.");
        setAiIsFallback(true);
      })
      .finally(() => {
        setAiLoading(false);
      });
  }, [activeDataset]);

  return (
    <div className="space-y-6">
      {/* Active Dataset & Scope Clarification Banner */}
      <div className="saas-card p-5 bg-white dark:bg-[#090e17] border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider bg-emerald-50 dark:bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-500/20">
              Active Cohort Scope
            </span>
            <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">
              {activeDataset ? activeDataset.semester : "Loading"}
            </span>
            {/* Scope Telemetry Badge */}
            <span className="text-[10px] text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 flex items-center gap-1 font-mono">
              <Database className="h-3 w-3 text-emerald-500" />
              <span>
                {scopes
                  ? `${scopes.saved_cohorts_count} Cohorts in DB (${scopes.total_students_across_all_cohorts} Total Synthetic Records)`
                  : `${datasets.length} Saved Cohorts`}
              </span>
            </span>
          </div>

          <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <span>{activeDataset ? activeDataset.name : "Loading Cohort..."}</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Active Cohort: <span className="text-slate-900 dark:text-white font-semibold">{activeDataset?.num_students || 0} Students</span> •{" "}
            Weekly Records: <span className="text-emerald-600 dark:text-emerald-400 font-semibold font-mono">{((activeDataset?.num_students || 0) * (activeDataset?.num_weeks || 0)).toLocaleString()}</span> •{" "}
            {activeDataset?.institution_name && (
              <span className="text-slate-700 dark:text-slate-300 font-medium">{activeDataset.institution_name} • </span>
            )}
            Profile: <span className="text-slate-700 dark:text-slate-300 font-medium">{activeDataset?.profile}</span> •{" "}
            {activeDataset?.num_weeks} Weeks • 100% Synthetic (FERPA Safe)
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/generator"
            className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 px-3.5 py-2 rounded-lg text-xs font-semibold border border-slate-200 dark:border-slate-700 transition"
          >
            <Sliders className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
            <span>Generate New</span>
          </Link>
          <Link
            href="/ai-insights"
            className="flex items-center gap-1.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white px-3.5 py-2 rounded-lg text-xs font-semibold shadow-sm shadow-emerald-600/30 transition"
          >
            <Bot className="h-3.5 w-3.5" />
            <span>AI Diagnostic</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <KPICard
          title="Cohort Students"
          value={kpis?.total_students || 0}
          subtitle={`Active cohort: ${activeDataset?.name?.slice(0, 20)}...`}
          icon={Users}
          variant="default"
        />
        <KPICard
          title="Avg Attendance"
          value={`${kpis?.avg_attendance || 0}%`}
          subtitle={`${kpis?.chronic_absent_count || 0} students under 60%`}
          icon={CalendarCheck2}
          variant={(kpis?.avg_attendance || 0) < 70 ? "warning" : "success"}
        />
        <KPICard
          title="Engagement Index"
          value={`${kpis?.avg_engagement || 0}`}
          subtitle="Cohort mean (0-100 scale)"
          icon={TrendingUp}
          variant={(kpis?.avg_engagement || 0) < 55 ? "danger" : "default"}
        />
        <KPICard
          title="High-Risk Flagged"
          value={kpis?.high_risk_count || 0}
          subtitle="Tier 3 counselor outreach"
          icon={AlertTriangle}
          variant={(kpis?.high_risk_count || 0) > 40 ? "danger" : "warning"}
        />
        <KPICard
          title="Assignment Completion"
          value={`${kpis?.avg_assignment_completion || 0}%`}
          subtitle={`Avg score: ${kpis?.avg_marks || 0}% marks`}
          icon={CheckCircle2}
          variant="success"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Weekly Trend Line Chart */}
        <div className="saas-card p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Longitudinal Engagement Trajectory
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                16-Week active cohort mean engagement index vs attendance percentage
              </p>
            </div>
            <span className="text-[11px] font-mono text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-500/20">
              Weekly Mean
            </span>
          </div>
          <WeeklyTrendChart data={trends} />
        </div>

        {/* Engagement Tier Distribution Donut */}
        <div className="saas-card p-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Engagement Distribution
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">High (≥75) • Medium (50-74) • Low (&lt;50)</p>
            </div>
          </div>
          <DonutDistributionChart
            data={distributions?.engagement_distribution || []}
            title="Engagement Tiers"
          />
        </div>
      </div>

      {/* Second Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Attendance Distribution */}
        <div className="saas-card p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200 mb-1">
            Attendance Distribution
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-2">Binned active student distribution across attendance rates</p>
          <DistributionBarChart
            data={distributions?.attendance_distribution || []}
            xKey="bin"
            barKey="count"
            barName="Students"
            color="#10b981"
          />
        </div>

        {/* Course-Wise Engagement Comparison */}
        <div className="saas-card p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200 mb-1">
            Course-Wise Engagement
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-2">Average composite score per course</p>
          <DistributionBarChart
            data={distributions?.course_breakdown || []}
            xKey="course"
            barKey="engagement"
            barName="Avg Engagement"
            color="#059669"
          />
        </div>

        {/* Risk Distribution Donut */}
        <div className="saas-card p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200 mb-1">
            Academic Risk Levels
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-2">Early Warning Tier Classification</p>
          <DonutDistributionChart
            data={distributions?.risk_distribution || []}
            title="Risk Breakdown"
          />
        </div>
      </div>

      {/* Bottom Section: Priority Attention Students & Executive AI Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Priority Attention Table */}
        <div className="saas-card p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
                <span>Priority Attention Queue</span>
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Top students flagged by Early Warning System heuristics
              </p>
            </div>
            <Link
              href="/early-warning"
              className="text-xs text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 flex items-center gap-1 font-semibold transition"
            >
              <span>View All Flags</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-[#090d16] text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-2 px-3 font-medium">Student ID</th>
                  <th className="py-2 px-3 font-medium">Risk Level</th>
                  <th className="py-2 px-3 font-medium">Attendance</th>
                  <th className="py-2 px-3 font-medium">Risk Score</th>
                  <th className="py-2 px-3 font-medium">Primary Trigger</th>
                  <th className="py-2 px-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/60 dark:divide-slate-800/60">
                {flaggedStudents.map((stu) => (
                  <tr key={stu.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-900 dark:text-white">
                      {stu.id}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          stu.risk_level === "High"
                            ? "bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/30"
                            : stu.risk_level === "Medium"
                            ? "bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30"
                            : "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30"
                        }`}
                      >
                        {stu.risk_level}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono">{stu.attendance_pct}%</td>
                    <td className="py-2.5 px-3 font-mono font-medium">{stu.risk_score}</td>
                    <td className="py-2.5 px-3">
                      <span className="text-[11px] text-slate-600 dark:text-slate-400 truncate max-w-[120px] block">
                        {stu.flagged_reasons?.[0] || "Multiple triggers"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => setSelectedStudentId(stu.id)}
                        className="text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 text-[11px] font-semibold transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
                {flaggedStudents.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-slate-500">
                      No high-risk students flagged.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Executive AI / Local Summary Card */}
        <div className="saas-card p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                  <Sparkles className="h-4 w-4" />
                </div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  {aiIsFallback ? "Local Cohort Synthesis" : "Groq AI Synthesis"}
                </h3>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded border font-medium ${
                  aiIsFallback
                    ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                    : "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30"
                }`}
              >
                {aiIsFallback ? "Local Heuristic" : "Groq Active"}
              </span>
            </div>

            <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-3">
              {aiIsFallback
                ? "Computed on-device using cohort summary statistics"
                : "Automated pedagogical diagnostic powered by Groq API"}
            </p>

            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-slate-200 leading-relaxed max-h-64 overflow-y-auto">
              {aiLoading ? (
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 py-6 justify-center">
                  <div className="h-4 w-4 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
                  <span>Synthesizing cohort diagnosis...</span>
                </div>
              ) : (
                <MarkdownRenderer content={aiSummary} />
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <span className="text-[10px] text-slate-500">Zero-PII Compliance</span>
            <Link
              href="/ai-insights"
              className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 flex items-center gap-1 transition"
            >
              <span>Open AI Co-Pilot</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* Student Dossier Drawer Modal */}
      {selectedStudentId && (
        <StudentDrawer
          studentId={selectedStudentId}
          datasetId={activeDataset?.id}
          onClose={() => setSelectedStudentId(null)}
        />
      )}
    </div>
  );
}
