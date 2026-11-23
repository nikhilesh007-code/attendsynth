"use client";

import React, { useState } from "react";
import {
  Settings,
  Sparkles,
  Database,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Server,
  Key,
  Clock,
  AlertTriangle,
  FolderOpen,
  Cpu,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { AITestConnectionResponse } from "@/types";

export default function SettingsPage() {
  const {
    apiHealthy,
    groqConfigured,
    groqStatus,
    groqModel,
    datasets,
    scopes,
    refreshDatasets,
    testGroq,
  } = useDataset();

  const [testingGroq, setTestingGroq] = useState(false);
  const [testResult, setTestResult] = useState<AITestConnectionResponse | null>(null);

  const handleTestGroq = async () => {
    try {
      setTestingGroq(true);
      setTestResult(null);
      const res = await testGroq(groqModel);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        success: false,
        status: "Groq Temporarily Unavailable",
        message: err.message || "Connection failed.",
      });
    } finally {
      setTestingGroq(false);
    }
  };

  const activeCount = scopes?.active_cohort_students ?? (datasets.find((d) => d.is_active)?.num_students || 0);
  const totalCount = scopes?.total_students_across_all_cohorts ?? datasets.reduce((acc, d) => acc + d.num_students, 0);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Settings className="h-5 w-5 text-indigo-400" />
            System & Engine Settings
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            API connections, environment configuration, database telemetry, and FERPA compliance.
          </p>
        </div>
        <button
          onClick={() => refreshDatasets()}
          className="text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 transition self-start sm:self-auto"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Groq Cloud API Engine Status Card */}
      <div className="saas-card p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Key className="h-4 w-4 text-indigo-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
              Groq Cloud API Integration (Free Tier Optimized)
            </h3>
          </div>
          <span
            className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${
              groqStatus === "Groq Request Successful" || groqStatus === "Active"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : groqStatus.includes("Rate Limited")
                ? "bg-rose-500/10 text-rose-300 border-rose-500/30"
                : groqConfigured
                ? "bg-indigo-500/10 text-indigo-300 border-indigo-500/30"
                : "bg-amber-500/10 text-amber-300 border-amber-500/30"
            }`}
          >
            {groqStatus}
          </span>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          The Groq API powers real-time pedagogical diagnosis, early warning pattern detection, and MTSS intervention planning.
          Requests are optimized for the Free Tier using concise prompting and <code className="text-indigo-300 font-mono">max_tokens: 500</code>.
        </p>

        <div className="p-3 rounded-lg bg-[#090d16] border border-slate-800 space-y-2 text-xs">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-indigo-400" />
              Configured Model:
            </span>
            <span className="font-mono text-indigo-300 font-semibold">{groqModel}</span>
          </div>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="text-slate-400">Environment Variable:</span>
            <code className="text-slate-300 font-mono text-[11px]">GROQ_MODEL=openai/gpt-oss-20b</code>
          </div>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="text-slate-400">Output Quota Management:</span>
            <span className="text-emerald-400 font-medium">Bapped at 500 tokens / 0.3 temp</span>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-1">
          <button
            onClick={handleTestGroq}
            disabled={testingGroq}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg flex items-center gap-2 transition"
          >
            {testingGroq ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Pinging Groq Engine...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5" />
                <span>Test Live Groq Connection</span>
              </>
            )}
          </button>
        </div>

        {testResult && (
          <div
            className={`p-3.5 rounded-lg border text-xs font-mono space-y-1.5 ${
              testResult.success
                ? "bg-emerald-500/5 border-emerald-500/30 text-emerald-300"
                : testResult.status.includes("Rate Limited")
                ? "bg-rose-500/5 border-rose-500/30 text-rose-300"
                : "bg-amber-500/5 border-amber-500/30 text-amber-300"
            }`}
          >
            <div className="flex items-center justify-between font-semibold">
              <span className="flex items-center gap-1.5">
                {testResult.success ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-rose-400" />
                )}
                Status: {testResult.status}
              </span>
              {testResult.latency_ms && (
                <span className="flex items-center gap-1 text-[11px] text-slate-400 font-normal">
                  <Clock className="h-3 w-3" />
                  {testResult.latency_ms} ms
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-300">{testResult.message}</p>
            {testResult.retry_after && (
              <p className="text-[11px] text-rose-400">
                Quota exceeded. Rate limit window refreshes in: {testResult.retry_after}s
              </p>
            )}
          </div>
        )}
      </div>

      {/* Database Telemetry & Scope Distinction */}
      <div className="saas-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-emerald-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
              SQLite Database Telemetry & Cohort Scopes
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">backend/attendsynth.db</span>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          AttendSynth AI separates the <strong className="text-white">Active Cohort</strong> (the dataset currently loaded for analytics, risk modeling, and EWS) from <strong className="text-white">Total Saved Cohorts</strong> stored persistently in SQLite.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-lg bg-[#090d16] border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Active Cohort Students</span>
            <div className="text-xl font-bold font-mono text-white mt-0.5">{activeCount}</div>
            <div className="text-[10px] text-indigo-400 mt-1 truncate">
              {scopes?.active_cohort_name || "Active Session"}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-[#090d16] border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">All Saved Students</span>
            <div className="text-xl font-bold font-mono text-indigo-400 mt-0.5">{totalCount}</div>
            <div className="text-[10px] text-slate-400 mt-1">Across all cohorts</div>
          </div>

          <div className="p-3 rounded-lg bg-[#090d16] border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Saved Cohorts</span>
            <div className="text-xl font-bold font-mono text-white mt-0.5">{datasets.length}</div>
            <div className="text-[10px] text-slate-400 mt-1">SQLite Tables</div>
          </div>

          <div className="p-3 rounded-lg bg-[#090d16] border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Engine Health</span>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-0.5">
              {apiHealthy ? "Online" : "Offline"}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">FastAPI Backend</div>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-[#0e1629] border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
          <FolderOpen className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-white">Relational Integrity Verification:</span>
            <p className="text-[11px] text-slate-400">
              Every student record uses a globally unique, stable <code className="text-indigo-300">student_id</code> as the primary key. All weekly logs, attendance records, risk breakdowns, and longitudinal time-series are linked by foreign keys, ensuring duplicate fictional names never collide.
            </p>
          </div>
        </div>
      </div>

      {/* FERPA Zero-PII Compliance Statement */}
      <div className="saas-card p-5 space-y-3 bg-[#0d1424]">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
          <ShieldCheck className="h-4 w-4" />
          <span>FERPA & Student Privacy Compliance Guarantee</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          AttendSynth AI was designed from the ground up to solve educational data privacy barriers.
          100% of student identities, demographic names, course enrollments, attendance percentages,
          and marks are synthesized mathematically using Faker and latent Gaussian variables.
          No real educational records, student identities, or PII are ever collected or processed.
        </p>
      </div>
    </div>
  );
}
