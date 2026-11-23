"use client";

import React, { useState, useEffect } from "react";
import {
  Bot,
  Sparkles,
  Send,
  Download,
  Copy,
  Check,
  ShieldCheck,
  AlertTriangle,
  Clock,
  CheckCircle2,
  FileText,
  RefreshCw,
  Cpu,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { api } from "@/lib/api";
import { AIInsightResponse, AITestConnectionResponse } from "@/types";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";

const SUGGESTED_PROMPTS = [
  "Analyze cohort health, attendance distributions, and overall persistence risk.",
  "Identify the primary drivers pushing students into High-Risk early warning status.",
  "Which curriculum courses exhibit the lowest average engagement and what explains it?",
  "Formulate a structured 4-week Multi-Tiered System of Supports (MTSS) intervention plan.",
];

export default function AIInsightsPage() {
  const { activeDataset, groqConfigured, groqModel, testGroq } = useDataset();

  const [query, setQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState(groqModel || "openai/gpt-oss-20b");
  const [loading, setLoading] = useState(false);
  const [insight, setInsight] = useState<AIInsightResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Connection testing state
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<AITestConnectionResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // Sync selected model with context default
  useEffect(() => {
    if (groqModel) setSelectedModel(groqModel);
  }, [groqModel]);

  // Load default executive summary on start
  useEffect(() => {
    if (!activeDataset) return;
    setLoading(true);
    setQueryError(null);
    api
      .getExecutiveSummary(activeDataset.id)
      .then((res) => setInsight(res))
      .catch((err) => {
        console.error("Initial AI synthesis failed", err);
        setQueryError(err.message || "Failed to load initial cohort summary.");
      })
      .finally(() => setLoading(false));
  }, [activeDataset]);

  const handleSubmit = async (e?: React.FormEvent | React.KeyboardEvent) => {
    if (e?.preventDefault) e.preventDefault();
    if (!query.trim() || !activeDataset) return;

    try {
      setLoading(true);
      setQueryError(null);
      const res = await api.queryAI(query.trim(), activeDataset.id, selectedModel || undefined);
      setInsight(res);
    } catch (err: any) {
      const msg = typeof err === "string" ? err : err?.message ? String(err.message) : "AI Analysis Request Failed";
      setQueryError(msg.includes("[object Object]") ? "Request error. Please check your query." : msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPingTest = async () => {
    try {
      setTestingConnection(true);
      setTestResult(null);
      const res = await testGroq(selectedModel);
      setTestResult(res);
    } finally {
      setTestingConnection(false);
    }
  };

  const handlePromptClick = (promptText: string) => {
    setQuery(promptText);
  };

  const handleCopy = () => {
    if (!insight?.response) return;
    navigator.clipboard.writeText(insight.response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!insight?.response || !activeDataset) return;
    const blob = new Blob([insight.response], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `AttendSynth_AI_Report_${activeDataset.id}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Bot className="h-5 w-5 text-indigo-400" />
            Groq AI Pedagogical Insights Co-Pilot
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Zero-PII aggregate cohort analysis, early disengagement diagnostics, and MTSS intervention planning.
          </p>
        </div>

        {/* Real Test Connection Button & Badge */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunPingTest}
            disabled={testingConnection}
            className="flex items-center gap-1.5 text-xs bg-[#0e1629] hover:bg-slate-800 border border-slate-800 text-slate-200 px-3 py-1.5 rounded-lg transition"
          >
            {testingConnection ? (
              <RefreshCw className="h-3 w-3 animate-spin text-indigo-400" />
            ) : (
              <Cpu className="h-3 w-3 text-indigo-400" />
            )}
            <span>Test Groq Connection</span>
          </button>
        </div>
      </div>

      {/* Ping Test Result Banner */}
      {testResult && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center justify-between animate-in fade-in ${
            testResult.success
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : testResult.status === "Groq Rate Limited"
              ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
              : "bg-amber-500/10 border-amber-500/30 text-amber-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
            )}
            <div>
              <span className="font-semibold">{testResult.status}:</span> {testResult.message}
            </div>
          </div>
          {testResult.latency_ms && (
            <span className="font-mono text-[11px] text-slate-400 shrink-0">{testResult.latency_ms}ms</span>
          )}
        </div>
      )}

      {/* Aggregate Telemetry Sent to Groq (Privacy Transparency) */}
      <div className="saas-card p-4 bg-[#0d1424] border border-slate-800 text-xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-300 font-semibold">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>FERPA Compliant Zero-PII Context Transmitted</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">No Personal Identifiers Sent</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px] text-slate-400">
          <div>Cohort: <span className="text-white">{activeDataset?.name}</span></div>
          <div>Size: <span className="text-white">{activeDataset?.num_students} STUs</span></div>
          <div>Mean Attn: <span className="text-white">{activeDataset?.mean_attendance}%</span></div>
          <div>Mean Eng: <span className="text-white">{activeDataset?.mean_engagement}</span></div>
        </div>
      </div>

      {/* Query Error Notification */}
      {queryError && (
        <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
            <span>{queryError}</span>
          </div>
          <button
            onClick={() => setQueryError(null)}
            className="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Inquiry Form */}
      <div className="saas-card p-4 space-y-4">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <span>Ask AI Co-Pilot</span>
            </label>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[11px] text-slate-400">Inference Engine:</span>
              <span className="bg-[#090d16] border border-indigo-500/30 rounded px-2.5 py-1 text-xs text-indigo-300 font-mono flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                openai/gpt-oss-20b (Free Tier Optimized)
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (!loading && query.trim() && activeDataset) {
                    handleSubmit(e);
                  }
                }
              }}
              placeholder="e.g. What interventions would most effectively rescue the chronic absent students?"
              className="flex-1 bg-[#090d16] border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 transition shadow-sm shadow-indigo-600/30"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  <span>Analyze</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Suggested Prompts */}
        <div className="space-y-1.5">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            Suggested Pedagogical Questions:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handlePromptClick(prompt)}
                className="text-[11px] bg-[#090d16] hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 rounded-md px-2.5 py-1 transition text-left"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* AI / Fallback Report Card */}
      <div className="saas-card p-5 space-y-4">
        {/* Status Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-indigo-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
              {insight?.is_fallback ? "Local Statistical Analysis" : "Pedagogical Diagnostic Report"}
            </h3>

            {/* Honest Status Pills */}
            {insight && (
              <span
                className={`text-[10px] font-medium px-2 py-0.5 rounded border ${
                  insight.status === "Groq Request Successful" || insight.status === "Groq API Connected"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : insight.status === "Groq Rate Limited"
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                    : insight.status === "Local Fallback Active"
                    ? "bg-amber-500/10 text-amber-300 border-amber-500/30"
                    : "bg-slate-800 text-slate-300 border-slate-700"
                }`}
              >
                {insight.status === "Groq Request Successful" ? "Groq API Connected" : insight.status}
              </span>
            )}

            {insight?.model_used && !insight?.is_fallback && (
              <span className="text-[10px] font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-2 py-0.5 rounded">
                {insight.model_used}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition flex items-center gap-1 text-xs"
              title="Copy report markdown"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition flex items-center gap-1 text-xs"
              title="Download report as markdown"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export .md</span>
            </button>
          </div>
        </div>

        {/* Rate Limit Notice Banner if rate limited */}
        {insight?.status === "Groq Rate Limited" && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-2">
            <Clock className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Groq Free-Tier Rate Limit:</span> {insight.error}
              <div className="text-[11px] text-slate-300 mt-1">
                Displaying deterministic Local Statistical Analysis calculated directly on the backend.
              </div>
            </div>
          </div>
        )}

        {/* Markdown Rendered Body */}
        <div className="bg-[#090d16] p-5 rounded-lg border border-slate-800/80 max-h-[600px] overflow-y-auto">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
              <div className="h-5 w-5 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
              <span className="text-xs">Processing analytical synthesis...</span>
            </div>
          ) : insight?.response ? (
            <MarkdownRenderer content={insight.response} />
          ) : (
            <div className="text-slate-500 text-center py-10 text-xs">
              Submit an inquiry or select a suggested prompt above to generate analysis.
            </div>
          )}
        </div>

        {/* Tokens & Execution Footer */}
        {insight && (
          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-border/60">
            <span>
              {insight.is_fallback
                ? "Computed using local backend statistics"
                : insight.tokens_used
                ? `Groq completion tokens: ${insight.tokens_used} (max 400)`
                : "Zero-PII Groq Execution"}
            </span>
            <span>AttendSynth AI Pedagogical Engine</span>
          </div>
        )}
      </div>
    </div>
  );
}
