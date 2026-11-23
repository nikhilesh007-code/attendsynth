"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  User,
  AlertTriangle,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  Minus,
  Calendar,
  BookOpen,
  Activity,
  Layers,
} from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Student } from "@/types";
import { api } from "@/lib/api";

interface StudentDrawerProps {
  studentId: string | null;
  datasetId?: string;
  onClose: () => void;
}

export function StudentDrawer({ studentId, datasetId, onClose }: StudentDrawerProps) {
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!studentId) return;
    setLoading(true);
    api
      .getStudentDetail(studentId, datasetId)
      .then((data) => setStudent(data))
      .catch((err) => console.error("Failed to load student dossier", err))
      .finally(() => setLoading(false));
  }, [studentId, datasetId]);

  if (!studentId) return null;

  // Breakdown values with safe fallbacks
  const breakdown = student?.risk_breakdown || {
    attendance_deficit: 0,
    assignment_deficit: 0,
    marks_deficit: 0,
    participation_deficit: 0,
    behavior_penalty: 0,
  };

  const riskFactors = [
    {
      label: "Attendance Deficit",
      score: breakdown.attendance_deficit ?? 0,
      max: 30,
      color: "bg-rose-500",
      barBg: "bg-rose-500/20",
      benchmark: "< 85% attendance target",
    },
    {
      label: "Assignment Completion Deficit",
      score: breakdown.assignment_deficit ?? 0,
      max: 25,
      color: "bg-amber-500",
      barBg: "bg-amber-500/20",
      benchmark: "< 85% submission target",
    },
    {
      label: "Formative Marks Deficit",
      score: breakdown.marks_deficit ?? 0,
      max: 20,
      color: "bg-orange-500",
      barBg: "bg-orange-500/20",
      benchmark: "< 75% grade average target",
    },
    {
      label: "In-Class Participation Deficit",
      score: breakdown.participation_deficit ?? 0,
      max: 15,
      color: "bg-indigo-500",
      barBg: "bg-indigo-500/20",
      benchmark: "< 75 score threshold",
    },
    {
      label: "Behavioral & Decay Penalty",
      score: breakdown.behavior_penalty ?? 0,
      max: 10,
      color: "bg-purple-500",
      barBg: "bg-purple-500/20",
      benchmark: "Late work & multi-week trend decay",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="saas-card-glow w-full max-w-2xl bg-[#0b101e] border border-slate-700/80 rounded-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-[#0e1629]">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <User className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-base font-semibold text-white">{student?.name || "Loading..."}</h3>
                <span className="font-mono text-xs text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/30">
                  {student?.student_id || student?.id}
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                  <ShieldCheck className="h-3 w-3" />
                  Synthetic Identity • FERPA Safe
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                <BookOpen className="h-3.5 w-3.5 text-slate-500" />
                {student?.course} • {student?.semester}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 max-h-[78vh] overflow-y-auto">
          {loading ? (
            <div className="h-48 flex items-center justify-center text-xs text-slate-400">
              Loading student longitudinal record...
            </div>
          ) : student ? (
            <>
              {/* Primary Indicators Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-[#0e1526] border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Attendance</span>
                  <div className="text-lg font-bold text-white font-mono mt-0.5">
                    {student.attendance_pct}%
                  </div>
                  <div
                    className={`text-[10px] font-medium mt-1 ${
                      student.attendance_pct < 60 ? "text-rose-400" : "text-emerald-400"
                    }`}
                  >
                    {student.attendance_pct < 60 ? "Critical Deficit (<60%)" : "Target Range"}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#0e1526] border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Engagement</span>
                  <div className="text-lg font-bold text-indigo-400 font-mono mt-0.5">
                    {student.engagement_score} <span className="text-xs text-slate-500">/100</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">{student.engagement_level} Tier</div>
                </div>

                <div className="p-3 rounded-lg bg-[#0e1526] border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Early Warning Risk</span>
                  <div
                    className={`text-lg font-bold font-mono mt-0.5 ${
                      student.risk_level === "High"
                        ? "text-rose-400"
                        : student.risk_level === "Medium"
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {student.risk_score} <span className="text-xs text-slate-500">({student.risk_level})</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Diagnostic Score</div>
                </div>

                <div className="p-3 rounded-lg bg-[#0e1526] border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Trajectory</span>
                  <div className="flex items-center gap-1 text-sm font-semibold text-white mt-1">
                    {student.weekly_trajectory === "Improving" && (
                      <TrendingUp className="h-4 w-4 text-emerald-400" />
                    )}
                    {student.weekly_trajectory === "Declining" && (
                      <TrendingDown className="h-4 w-4 text-rose-400" />
                    )}
                    {student.weekly_trajectory === "Stable" && (
                      <Minus className="h-4 w-4 text-slate-400" />
                    )}
                    <span>{student.weekly_trajectory}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">Over Term</div>
                </div>
              </div>

              {/* Multi-Factor Risk Decomposition Meters */}
              <div className="p-4 rounded-lg bg-[#0e1526] border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-indigo-400" />
                    Early Warning Risk Factor Decomposition
                  </h4>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Total: <strong className="text-white">{student.risk_score}</strong> / 100 max
                  </span>
                </div>

                <div className="space-y-2.5 pt-1">
                  {riskFactors.map((factor, idx) => {
                    const pctOfMax = Math.min(100, Math.max(0, (factor.score / factor.max) * 100));
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-300 font-medium">{factor.label}</span>
                            <span className="text-[10px] text-slate-500 hidden sm:inline">
                              ({factor.benchmark})
                            </span>
                          </div>
                          <div className="font-mono text-xs">
                            <span className="text-white font-semibold">+{factor.score.toFixed(1)}</span>
                            <span className="text-slate-500"> / {factor.max} pts</span>
                          </div>
                        </div>
                        <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${factor.color}`}
                            style={{ width: `${pctOfMax}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
                <p className="text-[10px] text-slate-500 italic pt-1 border-t border-slate-800/80">
                  Risk scores are calibrated using bounded institutional deficit factors (sum of all 5 dimensions, strictly 0.0 - 100.0). No artificial clamping.
                </p>
              </div>

              {/* Longitudinal Time Series Chart */}
              <div className="p-4 rounded-lg bg-[#0e1526] border border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-indigo-400" />
                    Longitudinal Weekly Engagement History
                  </h4>
                  <span className="text-[10px] text-slate-500">Weekly Score Trend</span>
                </div>
                <div className="h-36 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={student.weekly_history.map((val, idx) => ({
                        week: `Wk ${idx + 1}`,
                        score: val,
                      }))}
                      margin={{ top: 5, right: 10, left: -25, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="week" stroke="#64748b" fontSize={10} tickLine={false} />
                      <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#090d16",
                          borderColor: "#1e293b",
                          fontSize: "11px",
                          color: "#fff",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="score"
                        name="Weekly Score"
                        stroke="#6366f1"
                        strokeWidth={2}
                        dot={{ r: 2.5, fill: "#6366f1" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Transparent Risk Indicators & Recommendation */}
              <div className="space-y-3">
                <div className="p-3.5 rounded-lg bg-rose-500/5 border border-rose-500/20">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-300 mb-2">
                    <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                    Transparent Diagnostic Flags
                  </div>
                  {student.flagged_reasons && student.flagged_reasons.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {student.flagged_reasons.map((flag, idx) => (
                        <span
                          key={idx}
                          className="text-[11px] font-medium bg-rose-500/10 text-rose-200 border border-rose-500/20 px-2 py-0.5 rounded"
                        >
                          {flag}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400">No critical risk triggers flagged.</span>
                  )}
                </div>

                <div className="p-3.5 rounded-lg bg-indigo-500/5 border border-indigo-500/20">
                  <div className="text-xs font-semibold text-indigo-300 mb-1 flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5 text-indigo-400" />
                    Multi-Tiered Support Protocol (MTSS)
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {student.support_recommendation || "Maintain Tier 1 standard curriculum engagement."}
                  </p>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
