"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { api } from "@/lib/api";
import { Student } from "@/types";
import { StudentDrawer } from "@/components/students/StudentDrawer";

export default function StudentAnalyticsPage() {
  const { activeDataset } = useDataset();

  const [students, setStudents] = useState<Student[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedCourse, setSelectedCourse] = useState("");
  const [selectedRisk, setSelectedRisk] = useState("");
  const [selectedEngagement, setSelectedEngagement] = useState("");
  const [sortBy, setSortBy] = useState("risk_score");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  // Drawer
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);

  const fetchStudents = async () => {
    if (!activeDataset) return;
    try {
      setLoading(true);
      const res = await api.getStudents({
        datasetId: activeDataset.id,
        search: search.trim() || undefined,
        course: selectedCourse || undefined,
        riskLevel: selectedRisk || undefined,
        engagementLevel: selectedEngagement || undefined,
        sortBy,
        sortOrder,
        page,
        pageSize,
      });
      setStudents(res.students);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error("Error fetching students", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [activeDataset, page, pageSize, selectedCourse, selectedRisk, selectedEngagement, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchStudents();
  };

  const toggleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
    setPage(1);
  };

  return (
    <div className="space-y-5">
      {/* Page Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="h-5 w-5 text-indigo-400" />
            Student Cohort Analytics & Roster
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Multivariable cohort table with granular student engagement telemetry and longitudinal histories.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Total in cohort: <span className="text-white font-bold">{total}</span> Students
        </div>
      </div>

      {/* Filter Bar */}
      <div className="saas-card p-3.5 flex flex-wrap items-center justify-between gap-3 bg-[#0d1424]">
        <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[240px] relative">
          <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by student name or STU ID..."
            className="w-full bg-[#090d16] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2">
          {/* Course filter */}
          <select
            value={selectedCourse}
            onChange={(e) => {
              setSelectedCourse(e.target.value);
              setPage(1);
            }}
            className="bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">All Courses</option>
            {activeDataset?.courses.map((c) => (
              <option key={c} value={c}>
                {c.split(":")[0]}
              </option>
            ))}
          </select>

          {/* Risk filter */}
          <select
            value={selectedRisk}
            onChange={(e) => {
              setSelectedRisk(e.target.value);
              setPage(1);
            }}
            className="bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">All Risk Tiers</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
          </select>

          {/* Engagement filter */}
          <select
            value={selectedEngagement}
            onChange={(e) => {
              setSelectedEngagement(e.target.value);
              setPage(1);
            }}
            className="bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">All Engagement</option>
            <option value="High">High (≥75)</option>
            <option value="Medium">Medium (50-74)</option>
            <option value="Low">Low (&lt;50)</option>
          </select>

          {/* Page size */}
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(parseInt(e.target.value));
              setPage(1);
            }}
            className="bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value={10}>10 / page</option>
            <option value={20}>20 / page</option>
            <option value={50}>50 / page</option>
          </select>
        </div>
      </div>

      {/* Main Students Table */}
      <div className="saas-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#090d16] text-slate-400 border-b border-border select-none">
              <tr>
                <th className="py-2.5 px-3 font-medium cursor-pointer" onClick={() => toggleSort("id")}>
                  <div className="flex items-center gap-1">
                    <span>Student ID</span>
                    <ArrowUpDown className="h-3 w-3 text-slate-600" />
                  </div>
                </th>
                <th className="py-2.5 px-3 font-medium cursor-pointer" onClick={() => toggleSort("name")}>
                  <div className="flex items-center gap-1">
                    <span>Name</span>
                    <ArrowUpDown className="h-3 w-3 text-slate-600" />
                  </div>
                </th>
                <th className="py-2.5 px-3 font-medium">Course</th>
                <th className="py-2.5 px-3 font-medium cursor-pointer" onClick={() => toggleSort("attendance_pct")}>
                  <div className="flex items-center gap-1">
                    <span>Attendance</span>
                    <ArrowUpDown className="h-3 w-3 text-slate-600" />
                  </div>
                </th>
                <th className="py-2.5 px-3 font-medium cursor-pointer" onClick={() => toggleSort("participation_score")}>
                  <div className="flex items-center gap-1">
                    <span>Participation</span>
                    <ArrowUpDown className="h-3 w-3 text-slate-600" />
                  </div>
                </th>
                <th className="py-2.5 px-3 font-medium cursor-pointer" onClick={() => toggleSort("assignment_completion_pct")}>
                  <div className="flex items-center gap-1">
                    <span>Assignments</span>
                    <ArrowUpDown className="h-3 w-3 text-slate-600" />
                  </div>
                </th>
                <th className="py-2.5 px-3 font-medium cursor-pointer" onClick={() => toggleSort("engagement_score")}>
                  <div className="flex items-center gap-1">
                    <span>Engagement</span>
                    <ArrowUpDown className="h-3 w-3 text-slate-600" />
                  </div>
                </th>
                <th className="py-2.5 px-3 font-medium cursor-pointer" onClick={() => toggleSort("risk_score")}>
                  <div className="flex items-center gap-1">
                    <span>Risk Tier</span>
                    <ArrowUpDown className="h-3 w-3 text-slate-600" />
                  </div>
                </th>
                <th className="py-2.5 px-3 font-medium">Trajectory</th>
                <th className="py-2.5 px-3 font-medium text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-500">
                    Loading student records...
                  </td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-500">
                    No matching student records found.
                  </td>
                </tr>
              ) : (
                students.map((stu) => (
                  <tr
                    key={stu.id}
                    onClick={() => setSelectedStudentId(stu.id)}
                    className="hover:bg-slate-800/40 cursor-pointer transition group"
                  >
                    <td className="py-2.5 px-3 font-mono font-medium text-indigo-400">{stu.id}</td>
                    <td className="py-2.5 px-3 font-medium text-white">{stu.name}</td>
                    <td className="py-2.5 px-3 text-slate-300 max-w-[140px] truncate">{stu.course}</td>
                    <td className="py-2.5 px-3 font-mono">
                      <span className={stu.attendance_pct < 60 ? "text-rose-400 font-bold" : "text-slate-300"}>
                        {stu.attendance_pct}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{stu.participation_score}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{stu.assignment_completion_pct}%</td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-white">
                      {stu.engagement_score}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                          stu.risk_level === "High"
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            : stu.risk_level === "Medium"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        }`}
                      >
                        {stu.risk_level} ({stu.risk_score})
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-1 text-[11px] text-slate-400">
                        {stu.weekly_trajectory === "Improving" && (
                          <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                        )}
                        {stu.weekly_trajectory === "Declining" && (
                          <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
                        )}
                        {stu.weekly_trajectory === "Stable" && (
                          <Minus className="h-3.5 w-3.5 text-slate-500" />
                        )}
                        <span>{stu.weekly_trajectory}</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedStudentId(stu.id);
                        }}
                        className="p-1 rounded text-slate-400 group-hover:text-indigo-400 hover:bg-slate-800 transition"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 border-t border-border bg-[#090d16] flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <span className="text-white font-medium">{students.length > 0 ? (page - 1) * pageSize + 1 : 0}</span> to{" "}
            <span className="text-white font-medium">{Math.min(page * pageSize, total)}</span> of{" "}
            <span className="text-white font-medium">{total}</span> students
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded border border-slate-800 disabled:opacity-40 hover:bg-slate-800 transition text-slate-300"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="px-2 font-mono text-slate-300">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded border border-slate-800 disabled:opacity-40 hover:bg-slate-800 transition text-slate-300"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
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
