"use client";

import React, { useState, useEffect } from "react";
import {
  Building2,
  BookOpen,
  GraduationCap,
  Plus,
  Search,
  Filter,
  Edit2,
  Trash2,
  CheckCircle2,
  AlertCircle,
  X,
  Layers,
  MapPin,
  RefreshCw,
  Clock,
} from "lucide-react";
import { api } from "@/lib/api";
import { Institution, Department, Course } from "@/types";

export default function CurriculumPage() {
  const [activeTab, setActiveTab] = useState<"courses" | "institutions" | "departments">("courses");

  // Data states
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Filters for courses
  const [courseSearch, setCourseSearch] = useState("");
  const [selectedDeptFilter, setSelectedDeptFilter] = useState<string>("");
  const [selectedSemesterFilter, setSelectedSemesterFilter] = useState<string>("");

  // Modals
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [courseForm, setCourseForm] = useState({
    code: "",
    name: "",
    department_id: "",
    semester: "Semester 1",
    credits: 3,
    description: "",
  });

  const [showInstModal, setShowInstModal] = useState(false);
  const [editingInst, setEditingInst] = useState<Institution | null>(null);
  const [instForm, setInstForm] = useState({
    name: "",
    type: "University",
    location: "",
    description: "",
  });

  const [showDeptModal, setShowDeptModal] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [deptForm, setDeptForm] = useState({
    name: "",
    institution_id: "",
  });

  // Load all data
  const loadData = async () => {
    setLoading(true);
    try {
      const [instList, deptList, crsList] = await Promise.all([
        api.getInstitutions(),
        api.getDepartments(),
        api.getCourses(),
      ]);
      setInstitutions(instList);
      setDepartments(deptList);
      setCourses(crsList);
    } catch (err: any) {
      setActionMessage({ type: "error", text: err.message || "Failed to load curriculum data." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showNotification = (type: "success" | "error", text: string) => {
    setActionMessage({ type, text });
    setTimeout(() => setActionMessage(null), 4500);
  };

  // -------------------------------------------------------------
  // Course Handlers
  // -------------------------------------------------------------
  const handleOpenCourseModal = (course?: Course) => {
    if (course) {
      setEditingCourse(course);
      setCourseForm({
        code: course.code,
        name: course.name,
        department_id: course.department_id || "",
        semester: course.semester || "Semester 1",
        credits: course.credits || 3,
        description: course.description || "",
      });
    } else {
      setEditingCourse(null);
      setCourseForm({
        code: "",
        name: "",
        department_id: departments[0]?.id || "",
        semester: "Semester 1",
        credits: 3,
        description: "",
      });
    }
    setShowCourseModal(true);
  };

  const handleSaveCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingCourse) {
        await api.updateCourse(editingCourse.id, courseForm);
        showNotification("success", `Course '${courseForm.code}' updated successfully.`);
      } else {
        await api.createCourse(courseForm);
        showNotification("success", `Course '${courseForm.code}' created successfully.`);
      }
      setShowCourseModal(false);
      loadData();
    } catch (err: any) {
      showNotification("error", err.message || "Operation failed.");
    }
  };

  const handleDeleteCourse = async (id: string, code: string) => {
    if (!confirm(`Are you sure you want to delete course ${code}?`)) return;
    try {
      await api.deleteCourse(id);
      showNotification("success", `Course ${code} deleted.`);
      loadData();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to delete course.");
    }
  };

  // -------------------------------------------------------------
  // Institution Handlers
  // -------------------------------------------------------------
  const handleOpenInstModal = (inst?: Institution) => {
    if (inst) {
      setEditingInst(inst);
      setInstForm({
        name: inst.name,
        type: inst.type || "University",
        location: inst.location || "",
        description: inst.description || "",
      });
    } else {
      setEditingInst(null);
      setInstForm({
        name: "",
        type: "University",
        location: "",
        description: "",
      });
    }
    setShowInstModal(true);
  };

  const handleSaveInst = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingInst) {
        await api.updateInstitution(editingInst.id, instForm);
        showNotification("success", `Institution '${instForm.name}' updated.`);
      } else {
        await api.createInstitution(instForm);
        showNotification("success", `Institution '${instForm.name}' created.`);
      }
      setShowInstModal(false);
      loadData();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to save institution.");
    }
  };

  const handleDeleteInst = async (id: string, name: string) => {
    if (!confirm(`Delete institution '${name}'? This will delete associated departments.`)) return;
    try {
      await api.deleteInstitution(id);
      showNotification("success", `Institution '${name}' deleted.`);
      loadData();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to delete institution.");
    }
  };

  // -------------------------------------------------------------
  // Department Handlers
  // -------------------------------------------------------------
  const handleOpenDeptModal = (dept?: Department) => {
    if (dept) {
      setEditingDept(dept);
      setDeptForm({
        name: dept.name,
        institution_id: dept.institution_id,
      });
    } else {
      setEditingDept(null);
      setDeptForm({
        name: "",
        institution_id: institutions[0]?.id || "",
      });
    }
    setShowDeptModal(true);
  };

  const handleSaveDept = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingDept) {
        await api.updateDepartment(editingDept.id, deptForm);
        showNotification("success", `Department '${deptForm.name}' updated.`);
      } else {
        await api.createDepartment(deptForm);
        showNotification("success", `Department '${deptForm.name}' created.`);
      }
      setShowDeptModal(false);
      loadData();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to save department.");
    }
  };

  const handleDeleteDept = async (id: string, name: string) => {
    if (!confirm(`Delete department '${name}'?`)) return;
    try {
      await api.deleteDepartment(id);
      showNotification("success", `Department '${name}' deleted.`);
      loadData();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to delete department.");
    }
  };

  // Filtered courses
  const filteredCourses = courses.filter((c) => {
    const matchesSearch =
      courseSearch === "" ||
      c.code.toLowerCase().includes(courseSearch.toLowerCase()) ||
      c.name.toLowerCase().includes(courseSearch.toLowerCase()) ||
      c.description.toLowerCase().includes(courseSearch.toLowerCase());
    const matchesDept = selectedDeptFilter === "" || c.department_id === selectedDeptFilter;
    const matchesSem = selectedSemesterFilter === "" || c.semester === selectedSemesterFilter;
    return matchesSearch && matchesDept && matchesSem;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Building2 className="h-5 w-5 text-indigo-400" />
            Curriculum, Institutions & Course Management
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Dynamic university hierarchies, academic departments, and customizable course catalogs.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 transition self-start sm:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Notification Banner */}
      {actionMessage && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center gap-2 animate-in fade-in duration-200 ${
            actionMessage.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-rose-500/10 border-rose-500/30 text-rose-300"
          }`}
        >
          {actionMessage.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
          )}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("courses")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
            activeTab === "courses"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <BookOpen className="h-4 w-4" />
          <span>Courses ({courses.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("institutions")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
            activeTab === "institutions"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <Building2 className="h-4 w-4" />
          <span>Institutions ({institutions.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("departments")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
            activeTab === "departments"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Departments ({departments.length})</span>
        </button>
      </div>

      {/* TAB 1: COURSES MANAGEMENT */}
      {activeTab === "courses" && (
        <div className="space-y-4">
          {/* Controls Bar: Search, Filters, Add Button */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#0d1424] p-3.5 rounded-xl border border-slate-800">
            <div className="flex flex-wrap items-center gap-2.5 flex-1">
              <div className="relative min-w-[200px] flex-1">
                <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by code, title, or keywords..."
                  value={courseSearch}
                  onChange={(e) => setCourseSearch(e.target.value)}
                  className="w-full bg-[#090d16] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
                />
              </div>

              {/* Department Filter */}
              <select
                value={selectedDeptFilter}
                onChange={(e) => setSelectedDeptFilter(e.target.value)}
                className="bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
              >
                <option value="">All Departments</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>

              {/* Semester Filter */}
              <select
                value={selectedSemesterFilter}
                onChange={(e) => setSelectedSemesterFilter(e.target.value)}
                className="bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
              >
                <option value="">All Semesters</option>
                <option value="Semester 1">Semester 1</option>
                <option value="Semester 2">Semester 2</option>
                <option value="Semester 3">Semester 3</option>
                <option value="Semester 4">Semester 4</option>
                <option value="Semester 5">Semester 5</option>
                <option value="Semester 6">Semester 6</option>
              </select>
            </div>

            <button
              onClick={() => handleOpenCourseModal()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition shrink-0"
            >
              <Plus className="h-4 w-4" />
              <span>Add Custom Course</span>
            </button>
          </div>

          {/* Courses Table */}
          <div className="saas-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#090d16] text-slate-400 border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3.5 font-medium">Code</th>
                    <th className="py-2.5 px-3.5 font-medium">Course Title</th>
                    <th className="py-2.5 px-3.5 font-medium">Department</th>
                    <th className="py-2.5 px-3.5 font-medium">Semester</th>
                    <th className="py-2.5 px-3.5 font-medium">Credits</th>
                    <th className="py-2.5 px-3.5 font-medium">Description</th>
                    <th className="py-2.5 px-3.5 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredCourses.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-slate-500">
                        No courses found matching the search criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredCourses.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-3.5 font-mono font-bold text-indigo-400">{c.code}</td>
                        <td className="py-3 px-3.5 font-medium text-white">{c.name}</td>
                        <td className="py-3 px-3.5 text-slate-300">
                          {c.department_name || (
                            <span className="text-slate-500 italic">Unassigned</span>
                          )}
                        </td>
                        <td className="py-3 px-3.5 text-slate-400 font-mono text-[11px]">{c.semester}</td>
                        <td className="py-3 px-3.5 text-slate-300 font-mono">{c.credits} cr</td>
                        <td className="py-3 px-3.5 text-slate-400 max-w-xs truncate text-[11px]">
                          {c.description || "—"}
                        </td>
                        <td className="py-3 px-3.5 text-right space-x-1.5 whitespace-nowrap">
                          <button
                            onClick={() => handleOpenCourseModal(c)}
                            className="p-1 rounded text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition"
                            title="Edit course"
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteCourse(c.id, c.code)}
                            className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                            title="Delete course"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: INSTITUTIONS MANAGEMENT */}
      {activeTab === "institutions" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Registered academic institutions governing synthetic cohort profiles and course structures.
            </p>
            <button
              onClick={() => handleOpenInstModal()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition"
            >
              <Plus className="h-4 w-4" />
              <span>Add Institution</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {institutions.map((inst) => (
              <div
                key={inst.id}
                className="saas-card p-5 space-y-3 border-slate-800 hover:border-slate-700 transition relative group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                      <GraduationCap className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white tracking-tight">{inst.name}</h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] font-mono text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                          {inst.type}
                        </span>
                        {inst.location && (
                          <span className="text-[11px] text-slate-400 flex items-center gap-1">
                            <MapPin className="h-3 w-3 text-slate-500" />
                            {inst.location}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenInstModal(inst)}
                      className="p-1.5 rounded text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition"
                      title="Edit"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteInst(inst.id, inst.name)}
                      className="p-1.5 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                      title="Delete"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  {inst.description || "No institutional description recorded."}
                </p>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                  <div className="flex items-center gap-3">
                    <span>
                      Departments: <strong className="text-white">{inst.departments_count}</strong>
                    </span>
                    <span>
                      Saved Cohorts: <strong className="text-white">{inst.cohorts_count}</strong>
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-slate-500">{inst.id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: DEPARTMENTS MANAGEMENT */}
      {activeTab === "departments" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Colleges and specialized academic departments offering courses and cohort tracks.
            </p>
            <button
              onClick={() => handleOpenDeptModal()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition"
            >
              <Plus className="h-4 w-4" />
              <span>Add Department</span>
            </button>
          </div>

          <div className="saas-card overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#090d16] text-slate-400 border-b border-border">
                <tr>
                  <th className="py-2.5 px-3.5 font-medium">Department Name</th>
                  <th className="py-2.5 px-3.5 font-medium">Parent Institution</th>
                  <th className="py-2.5 px-3.5 font-medium">Offered Courses</th>
                  <th className="py-2.5 px-3.5 font-medium">Department ID</th>
                  <th className="py-2.5 px-3.5 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {departments.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3.5 font-semibold text-white">{d.name}</td>
                    <td className="py-3 px-3.5 text-indigo-300 font-medium">
                      {d.institution_name || d.institution_id}
                    </td>
                    <td className="py-3 px-3.5 text-slate-300 font-mono">
                      {d.courses_count} courses
                    </td>
                    <td className="py-3 px-3.5 font-mono text-[10px] text-slate-500">{d.id}</td>
                    <td className="py-3 px-3.5 text-right space-x-1.5 whitespace-nowrap">
                      <button
                        onClick={() => handleOpenDeptModal(d)}
                        className="p-1 rounded text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteDept(d.id, d.name)}
                        className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: ADD / EDIT COURSE */}
      {showCourseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0b101e] border border-slate-700 rounded-xl w-full max-w-md p-6 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-indigo-400" />
                {editingCourse ? "Edit Course Record" : "Create Academic Course"}
              </h3>
              <button
                onClick={() => setShowCourseModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSaveCourse} className="space-y-4 pt-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Course Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. CS101, DS201"
                    value={courseForm.code}
                    onChange={(e) => setCourseForm({ ...courseForm, code: e.target.value })}
                    className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white font-mono uppercase focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Credits</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={courseForm.credits}
                    onChange={(e) => setCourseForm({ ...courseForm, credits: parseInt(e.target.value) || 3 })}
                    className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Course Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Programming Fundamentals"
                  value={courseForm.name}
                  onChange={(e) => setCourseForm({ ...courseForm, name: e.target.value })}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Department</label>
                  <select
                    value={courseForm.department_id}
                    onChange={(e) => setCourseForm({ ...courseForm, department_id: e.target.value })}
                    className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">None (Universal)</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Semester</label>
                  <select
                    value={courseForm.semester}
                    onChange={(e) => setCourseForm({ ...courseForm, semester: e.target.value })}
                    className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Semester 1">Semester 1</option>
                    <option value="Semester 2">Semester 2</option>
                    <option value="Semester 3">Semester 3</option>
                    <option value="Semester 4">Semester 4</option>
                    <option value="Semester 5">Semester 5</option>
                    <option value="Semester 6">Semester 6</option>
                    <option value="Semester 7">Semester 7</option>
                    <option value="Semester 8">Semester 8</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Course syllabus, core competencies..."
                  value={courseForm.description}
                  onChange={(e) => setCourseForm({ ...courseForm, description: e.target.value })}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCourseModal(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition"
                >
                  {editingCourse ? "Save Changes" : "Create Course"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADD / EDIT INSTITUTION */}
      {showInstModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0b101e] border border-slate-700 rounded-xl w-full max-w-md p-6 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Building2 className="h-4 w-4 text-indigo-400" />
                {editingInst ? "Edit Institution" : "Add Academic Institution"}
              </h3>
              <button
                onClick={() => setShowInstModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSaveInst} className="space-y-4 pt-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Institution Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. SRM Institute of Science and Technology"
                  value={instForm.name}
                  onChange={(e) => setInstForm({ ...instForm, name: e.target.value })}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Type</label>
                  <select
                    value={instForm.type}
                    onChange={(e) => setInstForm({ ...instForm, type: e.target.value })}
                    className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="University">University</option>
                    <option value="Public University">Public University</option>
                    <option value="College">College</option>
                    <option value="K-12 District">K-12 District</option>
                    <option value="EdTech Academy">EdTech Academy</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Location</label>
                  <input
                    type="text"
                    placeholder="e.g. Chennai, India"
                    value={instForm.location}
                    onChange={(e) => setInstForm({ ...instForm, location: e.target.value })}
                    className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Academic overview, accreditation..."
                  value={instForm.description}
                  onChange={(e) => setInstForm({ ...instForm, description: e.target.value })}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowInstModal(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition"
                >
                  {editingInst ? "Save Changes" : "Create Institution"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADD / EDIT DEPARTMENT */}
      {showDeptModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0b101e] border border-slate-700 rounded-xl w-full max-w-md p-6 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="h-4 w-4 text-indigo-400" />
                {editingDept ? "Edit Department" : "Create Academic Department"}
              </h3>
              <button
                onClick={() => setShowDeptModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSaveDept} className="space-y-4 pt-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Parent Institution *</label>
                <select
                  required
                  value={deptForm.institution_id}
                  onChange={(e) => setDeptForm({ ...deptForm, institution_id: e.target.value })}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  {institutions.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Department Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Department of Computer Science & Engineering"
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowDeptModal(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition"
                >
                  {editingDept ? "Save Changes" : "Create Department"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
