"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Database,
  PlusCircle,
  Download,
  Trash2,
  CheckCircle2,
  GitCompare,
  Edit2,
  FileSpreadsheet,
  FileText,
  FileCode,
  Calendar,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { api } from "@/lib/api";

export default function DatasetsPage() {
  const { datasets, activeDataset, selectDataset, refreshDatasets } = useDataset();

  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [compareId1, setCompareId1] = useState(datasets[0]?.id || "");
  const [compareId2, setCompareId2] = useState(datasets[1]?.id || datasets[0]?.id || "");
  const [compareResult, setCompareResult] = useState<any | null>(null);

  const handleExport = (datasetId: string, format: "csv" | "excel" | "json" | "weekly_csv") => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const url = `${apiBase}/datasets/${datasetId}/export/${format}`;
    window.open(url, "_blank");
  };

  const handleRename = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renamingId || !newName.trim()) return;

    try {
      await api.renameDataset(renamingId, newName.trim());
      await refreshDatasets();
      setRenamingId(null);
      setNewName("");
    } catch (err: any) {
      alert(`Rename error: ${err.message}`);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (datasets.length <= 1) {
      alert("Cannot delete the only remaining academic dataset.");
      return;
    }
    if (!confirm(`Are you sure you want to permanently delete cohort "${name}"?`)) return;

    try {
      await api.deleteDataset(id);
      await refreshDatasets();
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  const handleCompare = async () => {
    if (!compareId1 || !compareId2) return;
    try {
      const res = await api.compareDatasets(compareId1, compareId2);
      setCompareResult(res);
    } catch (err: any) {
      alert(`Comparison error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <Database className="h-5 w-5 text-emerald-500" />
            Dataset Management & SQLite Storage
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Persist, activate, export, rename, and compare multi-cohort synthetic academic datasets.
          </p>
        </div>
        <Link
          href="/generator"
          className="flex items-center gap-1.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm shadow-emerald-600/30 transition self-start sm:self-auto"
        >
          <PlusCircle className="h-3.5 w-3.5" />
          <span>New Cohort</span>
        </Link>
      </div>

      {/* Saved Datasets Table */}
      <div className="saas-card overflow-hidden">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-[#090e17]">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200">
            Stored Academic Cohorts ({datasets.length})
          </h3>
          <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
            SQLite Database: attendsynth.db
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-[#090d16] text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-2.5 px-3 font-medium">Status</th>
                <th className="py-2.5 px-3 font-medium">Dataset Name</th>
                <th className="py-2.5 px-3 font-medium">Profile</th>
                <th className="py-2.5 px-3 font-medium">Students</th>
                <th className="py-2.5 px-3 font-medium">Duration</th>
                <th className="py-2.5 px-3 font-medium">Mean Attendance</th>
                <th className="py-2.5 px-3 font-medium">High Risk</th>
                <th className="py-2.5 px-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/60 dark:divide-slate-800/60">
              {datasets.map((d) => {
                const isActive = activeDataset?.id === d.id;
                return (
                  <tr key={d.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3">
                      {isActive ? (
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-500/30 w-fit">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Active</span>
                        </span>
                      ) : (
                        <button
                          onClick={() => selectDataset(d.id)}
                          className="text-[11px] font-medium text-slate-700 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-300 bg-slate-100 hover:bg-emerald-50 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 px-2.5 py-0.5 rounded transition"
                        >
                          Activate
                        </button>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-900 dark:text-white">{d.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        {d.institution_name ? `${d.institution_name} • ` : ""}
                        {d.id} • {d.semester}
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">{d.profile}</td>
                    <td className="py-3 px-3 font-mono">
                      <span className="font-bold text-slate-900 dark:text-white">{d.num_students}</span>
                      <span className="text-[10px] text-slate-500 block">
                        {(d.num_students * d.num_weeks).toLocaleString()} w-logs
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600 dark:text-slate-300">{d.num_weeks} wks</td>
                    <td className="py-3 px-3 font-mono text-slate-600 dark:text-slate-300">{d.mean_attendance}%</td>
                    <td className="py-3 px-3 font-mono text-rose-600 dark:text-rose-400 font-bold">{d.high_risk_count}</td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {/* Export Menu */}
                        <button
                          onClick={() => handleExport(d.id, "csv")}
                          className="p-1 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition"
                          title="Export Students CSV"
                        >
                          <FileText className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleExport(d.id, "weekly_csv")}
                          className="p-1 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition"
                          title="Export Weekly History CSV"
                        >
                          <Calendar className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleExport(d.id, "excel")}
                          className="p-1 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition"
                          title="Export Full Excel (Students + Weekly Engagement Sheets)"
                        >
                          <FileSpreadsheet className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleExport(d.id, "json")}
                          className="p-1 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition"
                          title="Export Full JSON"
                        >
                          <FileCode className="h-3.5 w-3.5" />
                        </button>

                        {/* Rename */}
                        <button
                          onClick={() => {
                            setRenamingId(d.id);
                            setNewName(d.name);
                          }}
                          className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition"
                          title="Rename dataset"
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </button>

                        {/* Delete */}
                        <button
                          onClick={() => handleDelete(d.id, d.name)}
                          disabled={datasets.length <= 1}
                          className="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 disabled:opacity-30 transition"
                          title="Delete dataset"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rename Modal */}
      {renamingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <form
            onSubmit={handleRename}
            className="saas-card p-5 max-w-md w-full bg-white dark:bg-[#0d1424] border border-slate-200 dark:border-slate-800 space-y-4 shadow-2xl"
          >
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">Rename Dataset</h3>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full bg-slate-50 dark:bg-[#090d16] border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
              required
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setRenamingId(null)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 rounded-lg text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
              >
                Save Name
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Dataset Comparison Tool */}
      <div className="saas-card p-5 space-y-4 bg-white dark:bg-[#090e17] border border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <GitCompare className="h-4 w-4 text-emerald-500" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200">
            Side-by-Side Cohort Comparison Tool
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="space-y-1">
            <label className="text-[11px] text-slate-500 dark:text-slate-400">Baseline Cohort (A)</label>
            <select
              value={compareId1}
              onChange={(e) => setCompareId1(e.target.value)}
              className="w-full bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.num_students} STUs)
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] text-slate-500 dark:text-slate-400">Comparison Cohort (B)</label>
            <select
              value={compareId2}
              onChange={(e) => setCompareId2(e.target.value)}
              className="w-full bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.num_students} STUs)
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleCompare}
              className="w-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold py-1.5 px-3 rounded-lg border border-slate-200 dark:border-slate-700 transition"
            >
              Compare Cohorts
            </button>
          </div>
        </div>

        {compareResult && (
          <div className="p-4 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-800 space-y-3 pt-3">
            <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-200">Comparison Findings</h4>
            <div className="grid grid-cols-3 gap-3 text-center text-xs">
              <div className="p-3 rounded bg-white dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase">Attendance Delta</span>
                <div
                  className={`text-base font-bold font-mono mt-1 ${
                    compareResult.deltas.attendance_diff >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                  }`}
                >
                  {compareResult.deltas.attendance_diff > 0
                    ? `+${compareResult.deltas.attendance_diff}%`
                    : `${compareResult.deltas.attendance_diff}%`}
                </div>
              </div>

              <div className="p-3 rounded bg-white dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase">Engagement Delta</span>
                <div
                  className={`text-base font-bold font-mono mt-1 ${
                    compareResult.deltas.engagement_diff >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                  }`}
                >
                  {compareResult.deltas.engagement_diff > 0
                    ? `+${compareResult.deltas.engagement_diff}`
                    : `${compareResult.deltas.engagement_diff}`}{" "}
                  pts
                </div>
              </div>

              <div className="p-3 rounded bg-white dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase">High Risk Delta</span>
                <div
                  className={`text-base font-bold font-mono mt-1 ${
                    compareResult.deltas.high_risk_diff <= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                  }`}
                >
                  {compareResult.deltas.high_risk_diff > 0
                    ? `+${compareResult.deltas.high_risk_diff}`
                    : `${compareResult.deltas.high_risk_diff}`}{" "}
                  students
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
