"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sliders,
  Sparkles,
  Users,
  Calendar,
  Layers,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  GraduationCap,
  RefreshCw,
  Building2,
  BookOpen,
  TrendingUp,
  TrendingDown,
  Database,
} from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { api } from "@/lib/api";
import { Dataset, Student, Institution, Department, Course } from "@/types";

const POPULATION_PROFILES = [
  {
    id: "Balanced engagement",
    name: "Balanced Engagement",
    description: "Standard Gaussian bell curve. Representative distribution across high, medium, and low tiers.",
    badge: "Standard",
  },
  {
    id: "Mostly engaged",
    name: "Mostly Engaged Cohort",
    description: "Positively skewed motivation (μ=+0.9). High attendance (>85%), minimal late assignments.",
    badge: "Honor / AP",
  },
  {
    id: "At-risk-heavy",
    name: "At-Risk Heavy Cohort",
    description: "Negatively skewed motivation (μ=-0.9). Severe attendance deficits, chronic absence (>30%).",
    badge: "Intervention Target",
  },
  {
    id: "Improving engagement",
    name: "Improving Engagement Trend",
    description: "Students show positive longitudinal drift (+14 pts) over weeks through active support.",
    badge: "Positive Drift",
  },
  {
    id: "Declining engagement",
    name: "Declining Engagement Decay",
    description: "Multi-week engagement decay pattern (-16 pts) reflecting progressive academic disengagement.",
    badge: "Decay Pattern",
  },
  {
    id: "Random mixed population",
    name: "Multimodal Mixed Cohort",
    description: "Multimodal mixture distribution spanning diverse student demographics and performance levels.",
    badge: "Stress Test",
  },
];

export default function GeneratorPage() {
  const router = useRouter();
  const { refreshDatasets } = useDataset();

  // Institution & Curriculum data
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loadingCurriculum, setLoadingCurriculum] = useState(false);

  // Form states
  const [selectedInstitutionId, setSelectedInstitutionId] = useState<string>("");
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string>("");
  const [academicYear, setAcademicYear] = useState<string>("2026-2027");
  const [semester, setSemester] = useState<string>("Fall 2026");
  const [name, setName] = useState<string>("");
  const [numStudents, setNumStudents] = useState<number>(250);
  const [studentsInput, setStudentsInput] = useState<string>("250");
  const [numWeeks, setNumWeeks] = useState<number>(16);
  const [weeksInput, setWeeksInput] = useState<string>("16");
  const [profile, setProfile] = useState<string>("Balanced engagement");
  const [randomSeed, setRandomSeed] = useState<number>(42);
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[]>([]);

  // Generation status
  const [generating, setGenerating] = useState(false);
  const [progressStep, setProgressStep] = useState("");
  const [generatedDataset, setGeneratedDataset] = useState<Dataset | null>(null);
  const [previewStudents, setPreviewStudents] = useState<Student[]>([]);

  // Load Institutions, Departments, Courses
  useEffect(() => {
    const fetchCurriculum = async () => {
      setLoadingCurriculum(true);
      try {
        const [instList, deptList, crsList] = await Promise.all([
          api.getInstitutions(),
          api.getDepartments(),
          api.getCourses(),
        ]);
        setInstitutions(instList);
        setDepartments(deptList);
        setCourses(crsList);

        if (instList.length > 0) {
          setSelectedInstitutionId(instList[0].id);
        }
        if (crsList.length > 0) {
          setSelectedCourseIds(crsList.map((c) => c.id));
        }
      } catch (err) {
        console.error("Failed to load curriculum options", err);
      } finally {
        setLoadingCurriculum(false);
      }
    };
    fetchCurriculum();
  }, []);

  // Filter departments when institution changes
  const availableDepartments = departments.filter(
    (d) => !selectedInstitutionId || d.institution_id === selectedInstitutionId
  );

  // Update cohort name automatically if user hasn't typed custom
  useEffect(() => {
    const inst = institutions.find((i) => i.id === selectedInstitutionId);
    const dept = departments.find((d) => d.id === selectedDepartmentId);
    const instName = inst ? inst.name.split(" ")[0] : "Cohort";
    const deptName = dept ? dept.name.replace("Department of ", "").split("&")[0].trim() : "All-Dept";
    setName(`${instName} ${deptName} - ${semester} (${numStudents} STUs)`);
  }, [selectedInstitutionId, selectedDepartmentId, semester, numStudents, institutions, departments]);

  const handleToggleCourse = (courseId: string) => {
    if (selectedCourseIds.includes(courseId)) {
      if (selectedCourseIds.length > 1) {
        setSelectedCourseIds(selectedCourseIds.filter((id) => id !== courseId));
      }
    } else {
      setSelectedCourseIds([...selectedCourseIds, courseId]);
    }
  };

  const handleSelectAllCourses = () => {
    setSelectedCourseIds(courses.map((c) => c.id));
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setGenerating(true);
      setProgressStep("Sampling latent motivation distribution θ (NumPy)...");

      await new Promise((r) => setTimeout(r, 350));
      setProgressStep("Synthesizing correlated attendance, participation & LMS telemetry...");

      await new Promise((r) => setTimeout(r, 350));
      setProgressStep(`Generating ${numWeeks}-week longitudinal time-series (${numStudents * numWeeks} records)...`);

      const newDs = await api.generateDataset({
        name: name.trim() || undefined,
        institution_id: selectedInstitutionId || undefined,
        department_id: selectedDepartmentId || undefined,
        academic_year: academicYear,
        num_students: numStudents,
        num_weeks: numWeeks,
        course_ids: selectedCourseIds.length > 0 ? selectedCourseIds : undefined,
        semester,
        population_profile: profile,
        random_seed: randomSeed,
      });

      setProgressStep("Persisting cohort records into SQLite database...");
      setGeneratedDataset(newDs);

      // Fetch sample preview students
      const stuList = await api.getStudents({ datasetId: newDs.id, pageSize: 6 });
      setPreviewStudents(stuList.students);

      await refreshDatasets();
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
      setProgressStep("");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sliders className="h-5 w-5 text-indigo-400" />
            Synthetic Cohort Generator Studio
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Configure parameters to synthesize statistically correlated, longitudinally coherent student records.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/curriculum"
            className="text-xs text-indigo-300 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 px-3 py-1.5 rounded-lg border border-indigo-500/30 flex items-center gap-1.5 transition"
          >
            <Building2 className="h-3.5 w-3.5" />
            <span>Manage Curriculum & Courses</span>
          </Link>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-1.5 rounded-full border border-emerald-500/30">
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>Zero-PII • 100% Synthetic</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Controls */}
        <form onSubmit={handleGenerate} className="saas-card p-5 space-y-5 lg:col-span-2">
          {/* Institutional Hierarchy */}
          <div className="space-y-3 p-3.5 rounded-xl bg-[#090d16] border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-indigo-400" />
                Institutional Affiliation
              </span>
              <span className="text-[10px] text-slate-500 font-mono">Dynamic Hierarchy</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Select Institution</label>
                <select
                  value={selectedInstitutionId}
                  onChange={(e) => {
                    setSelectedInstitutionId(e.target.value);
                    setSelectedDepartmentId("");
                  }}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Universal / Standalone</option>
                  {institutions.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Academic Department</label>
                <select
                  value={selectedDepartmentId}
                  onChange={(e) => setSelectedDepartmentId(e.target.value)}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">All / General Department</option>
                  {availableDepartments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
              <div>
                <label className="block text-slate-400 mb-1">Academic Year</label>
                <select
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white font-mono focus:outline-none focus:border-indigo-500"
                >
                  <option value="2026-2027">2026-2027</option>
                  <option value="2025-2026">2025-2026</option>
                  <option value="2027-2028">2027-2028</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Semester Term</label>
                <select
                  value={semester}
                  onChange={(e) => setSemester(e.target.value)}
                  className="w-full bg-[#0e1629] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Fall 2026">Fall 2026</option>
                  <option value="Spring 2027">Spring 2027</option>
                  <option value="Semester 1">Semester 1</option>
                  <option value="Semester 2">Semester 2</option>
                  <option value="Semester 3">Semester 3</option>
                  <option value="Semester 4">Semester 4</option>
                </select>
              </div>
            </div>
          </div>

          {/* Cohort Name */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-300">Generated Cohort Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. SRM University - CSE Cohort 2026-27"
              className="w-full bg-[#090d16] border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
              required
            />
          </div>

          {/* Student Count Selector */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300">
                Cohort Size (Number of Students)
              </label>
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] text-slate-400">Custom:</span>
                <input
                  type="text"
                  inputMode="numeric"
                  value={studentsInput}
                  onChange={(e) => {
                    const raw = e.target.value.replace(/[^0-9]/g, "");
                    setStudentsInput(raw);
                    const v = parseInt(raw);
                    if (!isNaN(v) && v >= 1) {
                      setNumStudents(Math.min(5000, v));
                    }
                  }}
                  onBlur={() => {
                    const v = parseInt(studentsInput);
                    if (isNaN(v) || v < 1) {
                      setStudentsInput("50");
                      setNumStudents(50);
                    } else {
                      const clamped = Math.min(5000, Math.max(1, v));
                      setStudentsInput(String(clamped));
                      setNumStudents(clamped);
                    }
                  }}
                  className="w-20 bg-[#090d16] border border-slate-700 focus:border-indigo-500 rounded px-2 py-0.5 text-xs text-indigo-300 font-mono text-right focus:outline-none"
                />
                <span className="text-xs text-slate-400 font-mono">STUs</span>
              </div>
            </div>
            <div className="grid grid-cols-6 gap-2">
              {[50, 100, 250, 500, 1000, 2000].map((val) => (
                <button
                  type="button"
                  key={val}
                  onClick={() => {
                    setNumStudents(val);
                    setStudentsInput(String(val));
                  }}
                  className={`py-1.5 text-xs font-mono font-medium rounded-lg border transition ${
                    numStudents === val
                      ? "bg-indigo-600/20 text-indigo-300 border-indigo-500 shadow-sm shadow-indigo-500/20"
                      : "bg-[#090d16] text-slate-400 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>

          {/* Longitudinal Weeks & Random Seed */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-300">Time-Series Duration</label>
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] text-slate-400">Custom:</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={weeksInput}
                    onChange={(e) => {
                      const raw = e.target.value.replace(/[^0-9]/g, "");
                      setWeeksInput(raw);
                      const v = parseInt(raw);
                      if (!isNaN(v) && v >= 1) {
                        setNumWeeks(Math.min(32, v));
                      }
                    }}
                    onBlur={() => {
                      const v = parseInt(weeksInput);
                      if (isNaN(v) || v < 4) {
                        setWeeksInput("4");
                        setNumWeeks(4);
                      } else {
                        const clamped = Math.min(32, Math.max(4, v));
                        setWeeksInput(String(clamped));
                        setNumWeeks(clamped);
                      }
                    }}
                    className="w-16 bg-[#090d16] border border-slate-700 focus:border-indigo-500 rounded px-2 py-0.5 text-xs text-indigo-300 font-mono text-right focus:outline-none"
                  />
                  <span className="text-xs text-slate-400 font-mono">wks</span>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-1.5">
                {[4, 8, 12, 16].map((w) => (
                  <button
                    type="button"
                    key={w}
                    onClick={() => {
                      setNumWeeks(w);
                      setWeeksInput(String(w));
                    }}
                    className={`py-1.5 text-xs font-mono font-medium rounded-lg border transition ${
                      numWeeks === w
                        ? "bg-indigo-600/20 text-indigo-300 border-indigo-500 shadow-sm shadow-indigo-500/20"
                        : "bg-[#090d16] text-slate-400 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    {w}w
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
                <span>Random Seed (Reproducibility)</span>
              </label>
              <input
                type="number"
                value={randomSeed}
                onChange={(e) => setRandomSeed(parseInt(e.target.value) || 42)}
                className="w-full bg-[#090d16] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-indigo-500 transition"
              />
            </div>
          </div>

          {/* Population Profile Selection */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-300">Synthetic Population Profile</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {POPULATION_PROFILES.map((p) => {
                const isSelected = profile === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setProfile(p.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition relative ${
                      isSelected
                        ? "bg-indigo-500/10 border-indigo-500 text-white"
                        : "bg-[#090d16] border-slate-800 hover:border-slate-700 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold">{p.name}</span>
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          isSelected
                            ? "bg-indigo-500 text-white"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {p.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{p.description}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Dynamic Course Assignment Multi-Select */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5 text-indigo-400" />
                Assign Courses to Cohort ({selectedCourseIds.length} Selected)
              </label>
              <button
                type="button"
                onClick={handleSelectAllCourses}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 transition"
              >
                Select All
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {courses.map((course) => {
                const isChecked = selectedCourseIds.includes(course.id);
                return (
                  <div
                    key={course.id}
                    onClick={() => handleToggleCourse(course.id)}
                    className={`flex items-center justify-between p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                      isChecked
                        ? "bg-indigo-500/10 border-indigo-500/50 text-white"
                        : "bg-[#090d16] border-slate-800/80 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`h-4 w-4 rounded flex items-center justify-center border text-[10px] ${
                          isChecked
                            ? "bg-indigo-600 border-indigo-500 text-white"
                            : "border-slate-700 bg-slate-900"
                        }`}
                      >
                        {isChecked && "✓"}
                      </div>
                      <div>
                        <span className="font-mono font-bold text-indigo-300 mr-1.5">{course.code}:</span>
                        <span>{course.name}</span>
                      </div>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">{course.credits}cr</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Submit Action */}
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
            <div className="text-xs text-slate-400 font-mono">
              Generating: <span className="text-white font-bold">{numStudents}</span> students ×{" "}
              <span className="text-white font-bold">{numWeeks}</span> weeks ={" "}
              <span className="text-indigo-400 font-bold">{numStudents * numWeeks}</span> weekly records
            </div>

            <button
              type="submit"
              disabled={generating}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-5 py-2.5 rounded-lg flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition"
            >
              {generating ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Synthesize Academic Cohort</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Live Generation Telemetry & Preview Pane */}
        <div className="space-y-4">
          <div className="saas-card p-4 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5 text-indigo-400" />
              Generator Architecture
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              AttendSynth AI uses latent variable motivation modeling (latent trait &theta; ~ Gaussian Normal) to synthesize
              inter-dependent attendance, LMS telemetry, and assessment submissions without generating uncorrelated random noise.
            </p>

            <div className="space-y-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
              <div className="flex items-center justify-between text-slate-400">
                <span>Latent Motivation (&theta;):</span>
                <span className="text-indigo-300">Gaussian Normal</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>ID Serialization:</span>
                <span className="text-emerald-400">SYNTH-STU-&#123;HEX&#125;-XXXX</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Database Persistence:</span>
                <span className="text-white">SQLite 3 Relational</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Privacy Guarantee:</span>
                <span className="text-emerald-400 font-semibold">FERPA Zero-PII</span>
              </div>
            </div>
          </div>

          {/* Generation Progress Indicator */}
          {generating && (
            <div className="saas-card p-4 space-y-3 bg-[#0d1424] border-indigo-500/30 animate-pulse">
              <div className="flex items-center gap-2 text-xs font-semibold text-indigo-300">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                <span>Synthesis In Progress...</span>
              </div>
              <p className="text-xs font-mono text-slate-300">{progressStep}</p>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full animate-progress w-2/3" />
              </div>
            </div>
          )}

          {/* Generated Result Card */}
          {generatedDataset && !generating && (
            <div className="saas-card p-4 space-y-3 bg-emerald-500/5 border-emerald-500/30 animate-in fade-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Cohort Generated Successfully!</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded">
                  Active
                </span>
              </div>

              <div className="space-y-1 text-xs">
                <div className="font-semibold text-white truncate">{generatedDataset.name}</div>
                <p className="text-slate-400 text-[11px]">
                  {generatedDataset.num_students} Students • {generatedDataset.num_weeks} Weeks •{" "}
                  {generatedDataset.num_students * generatedDataset.num_weeks} Longitudinal Records
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-center">
                <div className="p-2 rounded bg-[#090d16] border border-slate-800">
                  <div className="text-[10px] text-slate-400">Mean Attn</div>
                  <div className="text-xs font-bold text-white mt-0.5">
                    {generatedDataset.mean_attendance}%
                  </div>
                </div>
                <div className="p-2 rounded bg-[#090d16] border border-slate-800">
                  <div className="text-[10px] text-slate-400">Mean Eng</div>
                  <div className="text-xs font-bold text-indigo-400 mt-0.5">
                    {generatedDataset.mean_engagement}
                  </div>
                </div>
                <div className="p-2 rounded bg-[#090d16] border border-slate-800">
                  <div className="text-[10px] text-slate-400">High Risk</div>
                  <div className="text-xs font-bold text-rose-400 mt-0.5">
                    {generatedDataset.high_risk_count}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <Link
                  href="/"
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium py-1.5 px-3 rounded-lg text-center flex items-center justify-center gap-1 transition"
                >
                  <span>View Dashboard</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <Link
                  href="/analytics"
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium py-1.5 px-3 rounded-lg text-center transition"
                >
                  Inspect Roster
                </Link>
              </div>
            </div>
          )}

          {/* Sample Student Preview Table */}
          {previewStudents.length > 0 && (
            <div className="saas-card p-3 space-y-2">
              <span className="text-[11px] font-semibold text-slate-300">
                Sample Synthesized Student Identities
              </span>
              <div className="space-y-1.5">
                {previewStudents.map((s) => (
                  <div
                    key={s.id}
                    className="p-2 rounded bg-[#090d16] border border-slate-800 text-[11px] flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold text-white">{s.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{s.student_id}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-indigo-400">{s.engagement_score} Eng</div>
                      <span
                        className={`text-[9px] px-1.5 py-0.2 rounded font-medium ${
                          s.risk_level === "High"
                            ? "bg-rose-500/20 text-rose-300"
                            : s.risk_level === "Medium"
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-emerald-500/20 text-emerald-300"
                        }`}
                      >
                        {s.risk_level} Risk
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
