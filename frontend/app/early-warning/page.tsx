"use client";

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Clock,
  BookOpen,
  UserCheck,
  TrendingDown,
  Info,
  ExternalLink,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { api } from "@/lib/api";
import { EarlyWarningSummary, EarlyWarningFlaggedStudent } from "@/types";
import { StudentDrawer } from "@/components/students/StudentDrawer";

export default function EarlyWarningPage() {
  const { activeDataset } = useDataset();
  const [summary, setSummary] = useState<EarlyWarningSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);

  useEffect(() => {
    if (!activeDataset) return;
    setLoading(true);
    api
      .getEarlyWarningSummary(activeDataset.id)
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [activeDataset]);

  const total = summary?.total_students || 1;
  const highPct = (((summary?.high_risk_count || 0) / total) * 100).toFixed(1);
  const medPct = (((summary?.medium_risk_count || 0) / total) * 100).toFixed(1);
  const lowPct = (((summary?.low_risk_count || 0) / total) * 100).toFixed(1);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-rose-400" />
            Early Warning System (EWS)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Transparent institutional rule-based risk classification & Multi-Tiered System of Supports (MTSS).
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/30">
          <ShieldAlert className="h-3.5 w-3.5" />
          <span>Rule-Based Heuristic Framework</span>
        </div>
      </div>

      {/* 3 Risk Tiers Headline Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div className="saas-card p-4 border-rose-500/30 bg-rose-500/5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-300 uppercase tracking-wider">Tier 3 • High Risk</span>
            <span className="text-xs font-mono font-bold text-rose-400 bg-rose-500/20 px-2 py-0.5 rounded">
              {highPct}%
            </span>
          </div>
          <div className="text-2xl font-bold text-white font-mono mt-2">
            {summary?.high_risk_count || 0}{" "}
            <span className="text-xs font-normal text-slate-400">Students</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Requires immediate 1-on-1 counselor outreach and individualized intervention plan.
          </p>
        </div>

        <div className="saas-card p-4 border-amber-500/30 bg-amber-500/5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-300 uppercase tracking-wider">Tier 2 • Moderate Risk</span>
            <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/20 px-2 py-0.5 rounded">
              {medPct}%
            </span>
          </div>
          <div className="text-2xl font-bold text-white font-mono mt-2">
            {summary?.medium_risk_count || 0}{" "}
            <span className="text-xs font-normal text-slate-400">Students</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Secondary targeted intervention: peer tutoring, study hall check-ins, automated SMS alerts.
          </p>
        </div>

        <div className="saas-card p-4 border-emerald-500/30 bg-emerald-500/5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider">Tier 1 • Low Risk</span>
            <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded">
              {lowPct}%
            </span>
          </div>
          <div className="text-2xl font-bold text-white font-mono mt-2">
            {summary?.low_risk_count || 0}{" "}
            <span className="text-xs font-normal text-slate-400">Students</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Universal core instruction: maintain routine course engagement and standard syllabus pacing.
          </p>
        </div>
      </div>

      {/* Transparent Triggers Breakdown Grid */}
      <div className="saas-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5 text-indigo-400" />
            Transparent Rule Breakdown & Trigger Counts
          </h3>
          <span className="text-[11px] text-slate-400">Deterministic Diagnostic Criteria</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {summary?.reasons_breakdown &&
            Object.entries(summary.reasons_breakdown).map(([label, count]) => {
              const pct = (((count as number) / total) * 100).toFixed(1);
              return (
                <div key={label} className="p-3 rounded-lg bg-[#090d16] border border-slate-800">
                  <div className="text-base font-bold text-white font-mono">{count as number}</div>
                  <div className="text-[10px] text-indigo-400 font-mono mt-0.5">{pct}% of cohort</div>
                  <div className="text-[11px] text-slate-300 font-medium mt-1 leading-snug line-clamp-2" title={label}>
                    {label}
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* MTSS Support Protocols Guidance */}
      <div className="saas-card p-5 space-y-3 bg-[#0d1424]">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <UserCheck className="h-4 w-4 text-emerald-400" />
          Multi-Tiered System of Supports (MTSS) Intervention Roadmap
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          {summary?.mtss_recommendations &&
            Object.entries(summary.mtss_recommendations).map(([tier, actions]) => (
              <div key={tier} className="p-3.5 rounded-lg bg-[#090d16] border border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-indigo-300">{tier}</span>
                <ul className="space-y-1.5 text-[11px] text-slate-400">
                  {actions.map((act, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-indigo-400 font-bold">•</span>
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
        </div>
      </div>

      {/* Priority Flagged Students Queue Table */}
      <div className="saas-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
              Priority Intervention Queue ({summary?.flagged_students.length || 0} Students)
            </h3>
            <p className="text-[11px] text-slate-400">
              Students categorized as High or Medium risk ranked by composite risk score
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#090d16] text-slate-400 border-b border-border">
              <tr>
                <th className="py-2.5 px-3 font-medium">Student</th>
                <th className="py-2.5 px-3 font-medium">Course</th>
                <th className="py-2.5 px-3 font-medium">Attendance</th>
                <th className="py-2.5 px-3 font-medium">Participation</th>
                <th className="py-2.5 px-3 font-medium">Assignments</th>
                <th className="py-2.5 px-3 font-medium">Late</th>
                <th className="py-2.5 px-3 font-medium">Risk Score</th>
                <th className="py-2.5 px-3 font-medium">Trigger Flags</th>
                <th className="py-2.5 px-3 font-medium text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-10 text-center text-slate-500">
                    Evaluating cohort rules...
                  </td>
                </tr>
              ) : summary?.flagged_students.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-10 text-center text-slate-500">
                    No students currently meet the risk thresholds.
                  </td>
                </tr>
              ) : (
                summary?.flagged_students.map((stu) => (
                  <tr
                    key={stu.id}
                    onClick={() => setSelectedStudentId(stu.id)}
                    className="hover:bg-slate-800/40 cursor-pointer transition group"
                  >
                    <td className="py-2.5 px-3 font-medium text-white">
                      <div>{stu.name}</div>
                      <div className="text-[10px] text-indigo-400 font-mono">{stu.id}</div>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 max-w-[130px] truncate">{stu.course}</td>
                    <td className="py-2.5 px-3 font-mono">
                      <span className={stu.attendance_pct < 60 ? "text-rose-400 font-bold" : "text-slate-300"}>
                        {stu.attendance_pct}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{stu.participation_score}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{stu.assignment_completion_pct}%</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{stu.late_submissions}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`font-mono font-bold px-2 py-0.5 rounded text-[10px] border ${
                          stu.risk_level === "High"
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        }`}
                      >
                        {stu.risk_score} ({stu.risk_level})
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="flex flex-wrap gap-1 max-w-[220px]">
                        {stu.flagged_reasons.slice(0, 2).map((r, i) => (
                          <span
                            key={i}
                            className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700 truncate"
                          >
                            {r}
                          </span>
                        ))}
                        {stu.flagged_reasons.length > 2 && (
                          <span className="text-[10px] text-slate-500">
                            +{stu.flagged_reasons.length - 2} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedStudentId(stu.id);
                        }}
                        className="text-indigo-400 hover:text-indigo-300 text-xs font-medium"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transparency & Scientific Disclaimer Note */}
      <div className="p-3.5 rounded-lg bg-[#0e162b] border border-slate-800 flex items-start gap-3 text-xs text-slate-400 leading-relaxed">
        <Info className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200">Scientific Transparency Notice:</span> Early Warning
          System scores represent deterministic heuristic criteria based on educational research benchmarks
          (attendance deficits, assignment dropout, and engagement decay). They provide actionable diagnostics
          for advisor outreach rather than claims of predictive certainty.
        </div>
      </div>

      {/* Student Dossier Drawer */}
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
