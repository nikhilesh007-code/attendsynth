// AttendSynth AI Frontend Controller

let currentCohort = null;
let currentStudentPage = 1;
let currentLimit = 25;
let charts = {};
let latestRocData = null;
let latestTimelineData = null;

// On DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSidebar();
  initDashboard();
});

async function initDashboard() {
  await loadCohortsList();
  await loadDbStats();
  await fetchCohortSummary();
  await loadStudents(1);
  await fetchModelMetrics();
  await loadPrivacyAndFidelity();
}

// ==========================================
// SQLITE DATABASE & COHORT MANAGEMENT
// ==========================================

async function loadCohortsList() {
  try {
    const res = await fetch("/api/cohorts");
    if (!res.ok) return;
    const cohorts = await res.json();
    const select = document.getElementById("activeCohortSelect");
    if (!select) return;
    select.innerHTML = "";
    cohorts.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.cohort_id;
      opt.innerText = `${c.cohort_name} (${c.student_count} STUs • ${c.total_weeks} Wks)`;
      if (c.is_active) opt.selected = true;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Error loading cohorts from DB:", err);
  }
}

async function switchCohortFromDropdown(cohortId) {
  if (!cohortId) return;
  try {
    const res = await fetch(`/api/cohorts/select/${cohortId}`, { method: "POST" });
    if (res.ok) {
      await fetchCohortSummary();
      await loadStudents(1);
      await fetchModelMetrics();
      await loadPrivacyAndFidelity();
      await loadDbStats();
    }
  } catch (err) {
    console.error("Error switching cohort:", err);
  }
}

async function loadDbStats() {
  try {
    const res = await fetch("/api/db/stats");
    if (!res.ok) return;
    const stats = await res.json();
    const tally = document.getElementById("dbTallyText");
    if (tally) {
      tally.innerText = `SQLite DB: ${stats.total_students} STUs (${stats.total_daily_records.toLocaleString()} rows • ${stats.db_file_size_kb} KB)`;
    }
  } catch (err) {
    console.error("Error loading DB stats:", err);
  }
}

// ==========================================
// THEME SWITCHER (Dark / White)
// ==========================================

function initTheme() {
  const isDark = document.documentElement.classList.contains("dark");
  updateThemeUI(isDark);
}

function toggleTheme() {
  const isDarkNow = document.documentElement.classList.contains("dark");
  const newDark = !isDarkNow;

  if (newDark) {
    document.documentElement.classList.add("dark");
    localStorage.setItem("attendsynth_theme", "dark");
  } else {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("attendsynth_theme", "light");
  }

  updateThemeUI(newDark);
  updateChartsTheme();
}

function updateThemeUI(isDark) {
  const btnText = document.getElementById("themeBtnText");
  if (btnText) {
    btnText.innerText = isDark ? "Theme: Dark" : "Theme: Light";
  }
}

function getChartColors() {
  const isDark = document.documentElement.classList.contains("dark");
  return {
    isDark,
    grid: isDark ? "#1e293b" : "#e2e8f0",
    text: isDark ? "#94a3b8" : "#64748b",
    legend: isDark ? "#94a3b8" : "#475569",
    doughnutBorder: isDark ? "#0f172a" : "#ffffff",
  };
}

function updateChartsTheme() {
  if (currentCohort && currentCohort.summary) {
    renderOverviewCharts(currentCohort.summary);
  }
  if (latestRocData) {
    renderRocCurve(latestRocData.points, latestRocData.auc);
  }
  if (latestTimelineData) {
    renderStudentTimelineChart(latestTimelineData);
  }
}

// ==========================================
// COLLAPSIBLE SIDEBAR CONTROLLER
// ==========================================

function initSidebar() {
  const savedState = localStorage.getItem("attendsynth_sidebar");
  const sidebar = document.getElementById("appSidebar");
  if (savedState === "collapsed" && sidebar) {
    sidebar.classList.add("sidebar-collapsed");
    updateSidebarToggleBtn(true);
  } else {
    updateSidebarToggleBtn(false);
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById("appSidebar");
  if (!sidebar) return;

  const isCollapsed = sidebar.classList.toggle("sidebar-collapsed");
  localStorage.setItem("attendsynth_sidebar", isCollapsed ? "collapsed" : "expanded");
  updateSidebarToggleBtn(isCollapsed);

  // Resize charts smoothly after sidebar transition
  setTimeout(() => {
    Object.values(charts).forEach(c => {
      if (c && typeof c.resize === "function") c.resize();
    });
  }, 300);
}

function updateSidebarToggleBtn(isCollapsed) {
  const btn = document.getElementById("sidebarToggleBtn");
  if (!btn) return;
  const label = btn.querySelector(".sidebar-label");
  if (label) {
    label.innerText = isCollapsed ? "Expand" : "Collapse Sidebar";
  }
}

function toggleMobileSidebar() {
  const sidebar = document.getElementById("appSidebar");
  const backdrop = document.getElementById("mobileBackdrop");
  if (!sidebar || !backdrop) return;

  const isHidden = sidebar.classList.contains("-translate-x-full");
  if (isHidden) {
    sidebar.classList.remove("-translate-x-full");
    backdrop.classList.remove("hidden");
  } else {
    sidebar.classList.add("-translate-x-full");
    backdrop.classList.add("hidden");
  }
}

// ==========================================
// TAB SWITCHING
// ==========================================

function switchTab(tabName) {
  document.querySelectorAll(".nav-tab").forEach(t => {
    t.classList.remove("active-tab");
  });
  const activeBtn = document.getElementById(`tab-${tabName}`);
  if (activeBtn) {
    activeBtn.classList.add("active-tab");
  }

  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
  const activePanel = document.getElementById(`panel-${tabName}`);
  if (activePanel) {
    activePanel.classList.remove("hidden");
  }

  // Close mobile sidebar if open
  const sidebar = document.getElementById("appSidebar");
  const backdrop = document.getElementById("mobileBackdrop");
  if (window.innerWidth < 768 && sidebar && !sidebar.classList.contains("-translate-x-full")) {
    toggleMobileSidebar();
  }

  // Trigger chart resizes if needed
  if (tabName === "overview" && charts.archetypeChart) {
    setTimeout(() => {
      charts.archetypeChart.resize();
      charts.riskTierChart.resize();
    }, 50);
  }
}

// ==========================================
// COHORT OVERVIEW & CHARTS
// ==========================================

async function fetchCohortSummary() {
  try {
    const res = await fetch("/api/cohorts/current");
    if (!res.ok) return;
    const data = await res.json();
    currentCohort = data;

    // Update Header
    const activeBadge = document.getElementById("activeCohortBadge");
    if (activeBadge) {
      activeBadge.innerText = `${data.cohort_name} (${data.summary.total_students} STUs)`;
    }
    const cohortSelect = document.getElementById("activeCohortSelect");
    if (cohortSelect && data.cohort_id) {
      cohortSelect.value = data.cohort_id;
    }
    if (data.config && data.config.district_name) {
      const distBadge = document.getElementById("activeDistrictBadge");
      if (distBadge) distBadge.innerText = data.config.district_name;
    }

    // Update KPIs safely
    const elTotal = document.getElementById("kpiTotalStudents");
    if (elTotal) elTotal.innerText = data.summary.total_students;
    const elAvgAtt = document.getElementById("kpiAvgAttendance");
    if (elAvgAtt) elAvgAtt.innerText = (data.summary.average_attendance_rate * 100).toFixed(1) + "%";
    const elChronic = document.getElementById("kpiChronicRate");
    if (elChronic) elChronic.innerText = (data.summary.chronic_absenteeism_rate * 100).toFixed(1) + "%";
    const elChronicCount = document.getElementById("kpiChronicCount");
    if (elChronicCount) elChronicCount.innerText = `${data.summary.chronic_absenteeism_count} students (≥10% missed)`;
    const elAvgLms = document.getElementById("kpiAvgLms");
    if (elAvgLms) elAvgLms.innerText = data.summary.average_daily_lms_minutes + "m";
    const elEarlyFlagged = document.getElementById("kpiEarlyFlagged");
    if (elEarlyFlagged) elEarlyFlagged.innerText = (data.summary.early_warning_flagged_pct * 100).toFixed(1) + "%";
    const elLeadTime = document.getElementById("kpiLeadTime");
    if (elLeadTime) elLeadTime.innerText = `Avg ~${Math.round(data.summary.average_early_warning_lead_time_days)}d lead time`;

    // Render Charts
    renderOverviewCharts(data.summary);
  } catch (err) {
    console.error("Error fetching cohort summary:", err);
  }
}

function renderOverviewCharts(summary) {
  const theme = getChartColors();

  // 1. Archetype Breakdown Chart
  const archLabels = {
    CONSISTENT_ACHIEVER: "Consistent Achiever",
    GRADUAL_DISENGAGER: "Gradual Disengager",
    SPORADIC_ATTENDEE: "Sporadic Attendee",
    LATE_SEMESTER_SLUMPER: "Late Slumper",
    CHRONIC_ABSENTEE: "Chronic Absentee",
    INTERVENTION_RESPONDER: "Interv. Responder",
  };

  const archKeys = Object.keys(summary.archetype_distribution);
  const archNames = archKeys.map(k => archLabels[k] || k);
  const archVals = archKeys.map(k => summary.archetype_distribution[k]);

  if (charts.archetypeChart) charts.archetypeChart.destroy();
  const ctxArch = document.getElementById("archetypeChart").getContext("2d");
  charts.archetypeChart = new Chart(ctxArch, {
    type: "bar",
    data: {
      labels: archNames,
      datasets: [{
        label: "Students",
        data: archVals,
        backgroundColor: [
          "#10b981", // green
          "#f59e0b", // amber
          "#06b6d4", // cyan
          "#6366f1", // indigo
          "#f43f5e", // rose
          "#14b8a6", // teal
        ],
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: theme.text, font: { size: 10 } }, grid: { display: false } },
        y: { ticks: { color: theme.text, font: { size: 10 } }, grid: { color: theme.grid } }
      }
    }
  });

  // 2. Risk Tier Donut Chart
  const riskLabels = ["LOW", "MODERATE", "ELEVATED", "CRITICAL"];
  const riskVals = riskLabels.map(r => summary.risk_distribution[r] || 0);

  if (charts.riskTierChart) charts.riskTierChart.destroy();
  const ctxRisk = document.getElementById("riskTierChart").getContext("2d");
  charts.riskTierChart = new Chart(ctxRisk, {
    type: "doughnut",
    data: {
      labels: ["Low Risk", "Moderate Risk", "Elevated Risk", "Critical Risk"],
      datasets: [{
        data: riskVals,
        backgroundColor: ["#10b981", "#06b6d4", "#f59e0b", "#f43f5e"],
        borderWidth: 2,
        borderColor: theme.doughnutBorder,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: theme.legend, font: { size: 11 }, padding: 12 }
        }
      },
      cutout: "65%",
    }
  });
}

// ==========================================
// STUDENT COHORT EXPLORER
// ==========================================

async function loadStudents(page = 1) {
  currentStudentPage = page;
  const search = document.getElementById("studentSearchInput").value;
  const risk = document.getElementById("studentRiskFilter").value;
  const arch = document.getElementById("studentArchFilter").value;

  const url = `/api/cohorts/current/students?page=${page}&limit=${currentLimit}&search=${encodeURIComponent(search)}&risk_level=${risk}&archetype=${arch}`;

  try {
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    const tbody = document.getElementById("studentTableBody");
    tbody.innerHTML = "";

    if (data.students.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-500">No matching synthetic students found.</td></tr>`;
      return;
    }

    data.students.forEach(s => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors";

      const riskPillColor = {
        CRITICAL: "bg-rose-500/10 text-rose-600 dark:text-rose-300 border-rose-500/30",
        ELEVATED: "bg-amber-500/10 text-amber-600 dark:text-amber-300 border-amber-500/30",
        MODERATE: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-300 border-cyan-500/30",
        LOW: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/30",
      }[s.risk_level] || "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300";

      const attPct = (s.attendance_rate * 100).toFixed(1);
      const subPct = (s.assignment_submission_rate * 100).toFixed(0);

      tr.innerHTML = `
        <td class="py-2.5 px-4 font-sans">
          <div class="font-bold text-slate-900 dark:text-slate-200 text-xs">${s.display_name}</div>
          <div class="text-slate-500 text-[10px] font-mono">${s.student_id}</div>
        </td>
        <td class="py-2.5 px-3 font-sans text-slate-700 dark:text-slate-300 text-xs overflow-hidden">
          <div class="font-medium truncate" title="${s.school_name}">${s.school_name}</div>
          <div class="text-[10px] text-slate-500 whitespace-nowrap">Grade ${s.grade_level} &bull; GPA ${s.baseline_gpa}</div>
        </td>
        <td class="py-2.5 px-3 font-sans text-xs text-slate-600 dark:text-slate-400 overflow-hidden">
          <div class="truncate" title="${s.archetype_label}">${s.archetype_label}</div>
        </td>
        <td class="py-2.5 px-3 text-xs text-center ${s.chronic_absenteeism_flag ? 'text-rose-600 dark:text-rose-400 font-bold' : 'text-emerald-600 dark:text-emerald-400'}">
          ${attPct}% ${s.chronic_absenteeism_flag ? '⚠️' : ''}
        </td>
        <td class="py-2.5 px-3 text-xs text-center text-slate-700 dark:text-slate-300">
          ${s.avg_daily_lms_minutes}m
        </td>
        <td class="py-2.5 px-3 text-xs text-center text-slate-700 dark:text-slate-300">
          ${subPct}%
        </td>
        <td class="py-2.5 px-3 text-center">
          <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${riskPillColor}">
            ${s.risk_level} (${Math.round(s.composite_risk_score)})
          </span>
        </td>
        <td class="py-2.5 px-3 text-right">
          <button onclick="viewStudentDetail('${s.student_id}')" class="px-2.5 py-1 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-emerald-600 dark:text-emerald-400 rounded-lg text-[11px] font-semibold border border-slate-200 dark:border-slate-700 shadow-sm transition-all">
            Inspect &rarr;
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Pagination info
    const startNum = (data.page - 1) * data.limit + 1;
    const endNum = Math.min(data.page * data.limit, data.total);
    document.getElementById("studentTablePaginationInfo").innerText = `Showing ${startNum}-${endNum} of ${data.total} students`;

    document.getElementById("btnPrevPage").disabled = data.page <= 1;
    document.getElementById("btnNextPage").disabled = endNum >= data.total;
  } catch (err) {
    console.error("Error loading students:", err);
  }
}

function changeStudentPage(delta) {
  loadStudents(currentStudentPage + delta);
}

// Student Detail Drawer
async function viewStudentDetail(studentId) {
  try {
    const res = await fetch(`/api/cohorts/current/students/${studentId}`);
    if (!res.ok) return;
    const data = await res.json();
    const s = data.student;
    const records = data.daily_timeline;
    latestTimelineData = records;

    const modal = document.getElementById("studentDetailModal");
    modal.classList.remove("hidden");
    modal.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("modalStudentName").innerText = s.display_name;
    document.getElementById("modalStudentID").innerText = s.student_id;
    document.getElementById("modalStudentMeta").innerText = `${s.school_name} • Grade ${s.grade_level} • Archetype: ${s.archetype_label} • Starting GPA: ${s.baseline_gpa}`;

    const riskBadge = document.getElementById("modalStudentRiskBadge");
    riskBadge.innerText = `${s.risk_level} RISK (Score: ${Math.round(s.composite_risk_score)})`;
    riskBadge.className = `text-xs font-semibold px-2 py-0.5 rounded-md ${
      s.risk_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-600 dark:text-rose-300' : (
        s.risk_level === 'ELEVATED' ? 'bg-amber-500/20 text-amber-600 dark:text-amber-300' : 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-300'
      )
    }`;

    // Intervention text
    document.getElementById("modalInterventionText").innerText = s.recommended_intervention.replace(/_/g, " ");
    document.getElementById("modalTriggerWeek").innerText = s.early_warning_trigger_week
      ? `🚨 EWS Signal Triggered at Week ${s.early_warning_trigger_week}`
      : `✓ On Track (No Early Warning)`;

    // Render Attendance Heatmap Grid
    const grid = document.getElementById("attendanceGrid");
    grid.innerHTML = "";
    records.forEach(r => {
      const tile = document.createElement("div");
      tile.className = "w-5 h-5 rounded day-tile cursor-pointer relative group flex items-center justify-center text-[9px] font-mono font-bold";

      const colorMap = {
        PRESENT: "bg-emerald-500 text-white",
        TARDY: "bg-amber-400 text-slate-950",
        EXCUSED_ABSENCE: "bg-cyan-500 text-white",
        UNEXCUSED_ABSENCE: "bg-rose-500 text-white font-bold",
      };
      tile.className += ` ${colorMap[r.attendance_status] || 'bg-slate-400'}`;
      tile.title = `${r.date} (Wk ${r.week_number}): ${r.attendance_status} | LMS: ${r.lms_active_minutes}m`;

      grid.appendChild(tile);
    });

    // Render Longitudinal Chart
    renderStudentTimelineChart(records);
  } catch (err) {
    console.error("Error viewing student detail:", err);
  }
}

function closeStudentModal() {
  document.getElementById("studentDetailModal").classList.add("hidden");
}

function renderStudentTimelineChart(records) {
  latestTimelineData = records;
  const theme = getChartColors();
  const labels = records.map(r => `W${r.week_number}-D${r.weekday + 1}`);
  const lmsData = records.map(r => r.lms_active_minutes);
  const quizScores = records.map(r => (r.quiz_score !== null && r.quiz_score > 0) ? r.quiz_score : null);

  if (charts.studentTimelineChart) charts.studentTimelineChart.destroy();
  const ctx = document.getElementById("studentTimelineChart").getContext("2d");

  charts.studentTimelineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Daily LMS Active Minutes",
          data: lmsData,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.12)",
          fill: true,
          tension: 0.3,
          pointRadius: 1.5,
          yAxisID: "y",
        },
        {
          label: "Quiz Scores",
          data: quizScores,
          borderColor: "#f59e0b",
          backgroundColor: "#f59e0b",
          showLine: false,
          pointRadius: 5,
          pointHoverRadius: 7,
          yAxisID: "y1",
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: theme.legend, font: { size: 10 } } }
      },
      scales: {
        x: { ticks: { color: theme.text, font: { size: 9 }, maxTicksLimit: 16 }, grid: { display: false } },
        y: {
          type: "linear",
          position: "left",
          ticks: { color: "#06b6d4", font: { size: 10 } },
          grid: { color: theme.grid },
          title: { display: true, text: "LMS Minutes", color: "#06b6d4", font: { size: 10 } }
        },
        y1: {
          type: "linear",
          position: "right",
          min: 0,
          max: 100,
          ticks: { color: "#f59e0b", font: { size: 10 } },
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Quiz Score", color: "#f59e0b", font: { size: 10 } }
        }
      }
    }
  });
}

// ==========================================
// MODEL LAB & ML TRAINING
// ==========================================

async function fetchModelMetrics() {
  try {
    const res = await fetch("/api/models/current");
    if (!res.ok) return;
    const m = await res.json();

    document.getElementById("metricRocAuc").innerText = m.roc_auc;
    document.getElementById("metricAccuracy").innerText = (m.accuracy * 100).toFixed(1) + "%";
    document.getElementById("metricPrecision").innerText = m.precision;
    document.getElementById("metricRecall").innerText = m.recall;

    // Confusion Matrix
    document.getElementById("cmTN").innerText = m.confusion_matrix.true_negative;
    document.getElementById("cmFP").innerText = m.confusion_matrix.false_positive;
    document.getElementById("cmFN").innerText = m.confusion_matrix.false_negative;
    document.getElementById("cmTP").innerText = m.confusion_matrix.true_positive;

    // Render ROC Curve
    renderRocCurve(m.roc_curve, m.roc_auc);

    // Feature Importances
    const fiContainer = document.getElementById("featureImportanceList");
    fiContainer.innerHTML = "";
    m.feature_importances.forEach(f => {
      const pct = Math.round(f.importance * 100);
      const row = document.createElement("div");
      row.className = "flex items-center justify-between";
      row.innerHTML = `
        <span class="text-slate-600 dark:text-slate-400 truncate max-w-[170px]">${f.feature.replace(/early_/g, "")}</span>
        <div class="flex items-center space-x-2 w-28">
          <div class="flex-1 bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div class="bg-emerald-500 h-full rounded-full" style="width: ${pct}%"></div>
          </div>
          <span class="text-emerald-600 dark:text-emerald-400 w-8 text-right font-mono font-semibold">${pct}%</span>
        </div>
      `;
      fiContainer.appendChild(row);
    });

    runLiveInference();
  } catch (err) {
    console.error("Error fetching model metrics:", err);
  }
}

async function trainMLModel() {
  const modelType = document.getElementById("mlModelType").value;
  const obsWeeks = parseInt(document.getElementById("mlObsWeeks").value);

  try {
    const res = await fetch("/api/models/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_type: modelType, observation_weeks: obsWeeks }),
    });
    if (!res.ok) {
      alert("Failed to train model.");
      return;
    }
    await fetchModelMetrics();
  } catch (err) {
    console.error("Error training model:", err);
  }
}

function renderRocCurve(rocPoints, aucVal) {
  if (!rocPoints || rocPoints.length === 0) return;
  latestRocData = { points: rocPoints, auc: aucVal };
  const theme = getChartColors();

  const dataPoints = rocPoints.map(p => ({ x: p.fpr, y: p.tpr }));

  if (charts.rocCurveChart) charts.rocCurveChart.destroy();
  const ctx = document.getElementById("rocCurveChart").getContext("2d");

  charts.rocCurveChart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [
        {
          label: `EWS Classifier (AUC = ${aucVal})`,
          data: dataPoints,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.15)",
          fill: true,
          tension: 0.1,
          pointRadius: 2,
        },
        {
          label: "Random Chance (AUC = 0.50)",
          data: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
          borderColor: theme.text,
          borderDash: [5, 5],
          pointRadius: 0,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: theme.legend, font: { size: 10 } } }
      },
      scales: {
        x: {
          type: "linear",
          min: 0,
          max: 1,
          title: { display: true, text: "False Positive Rate (1 - Specificity)", color: theme.legend, font: { size: 10 } },
          ticks: { color: theme.text },
          grid: { color: theme.grid }
        },
        y: {
          min: 0,
          max: 1,
          title: { display: true, text: "True Positive Rate (Sensitivity / Recall)", color: theme.legend, font: { size: 10 } },
          ticks: { color: theme.text },
          grid: { color: theme.grid }
        }
      }
    }
  });
}

// Live Inference Sandbox
async function runLiveInference() {
  const att = parseFloat(document.getElementById("simAtt").value);
  const tardy = parseFloat(document.getElementById("simTardy").value);
  const lms = parseFloat(document.getElementById("simLms").value);
  const decay = parseFloat(document.getElementById("simDecay").value);

  document.getElementById("simAttVal").innerText = Math.round(att * 100) + "%";
  document.getElementById("simTardyVal").innerText = Math.round(tardy * 100) + "%";
  document.getElementById("simLmsVal").innerText = lms + " mins";
  document.getElementById("simDecayVal").innerText = (decay >= 0 ? "+" : "") + Math.round(decay * 100) + "% drop";

  try {
    const res = await fetch("/api/models/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        early_attendance_rate: att,
        early_tardy_rate: tardy,
        early_unexcused_rate: tardy * 0.5,
        early_avg_daily_lms_minutes: lms,
        early_lms_trend_decay: decay,
        early_submission_rate: att * 0.95,
        early_quiz_average: 72.0,
        baseline_gpa: 2.8,
      })
    });
    if (!res.ok) return;
    const result = await res.json();

    const probPct = Math.round(result.predicted_risk_probability * 100);
    document.getElementById("simProbBadge").innerText = probPct + "%";
    document.getElementById("simTierBadge").innerText = result.predicted_risk_tier;
    document.getElementById("simActionText").innerText = result.recommended_action;

    const tierColors = {
      CRITICAL: "bg-rose-500/20 text-rose-600 dark:text-rose-300",
      ELEVATED: "bg-amber-500/20 text-amber-600 dark:text-amber-300",
      MODERATE: "bg-cyan-500/20 text-cyan-600 dark:text-cyan-300",
      LOW: "bg-emerald-500/20 text-emerald-600 dark:text-emerald-300",
    };
    document.getElementById("simTierBadge").className = `ml-3 px-2 py-0.5 rounded text-xs font-semibold ${tierColors[result.predicted_risk_tier] || ''}`;
  } catch (err) {
    console.error("Inference error:", err);
  }
}

// ==========================================
// PRIVACY & FIDELITY AUDIT
// ==========================================

async function loadPrivacyAndFidelity() {
  try {
    const [privRes, fidRes] = await Promise.all([
      fetch("/api/audit/privacy"),
      fetch("/api/audit/fidelity"),
    ]);

    if (privRes.ok) {
      const priv = await privRes.json();
      document.getElementById("privacyRatingBadge").innerText = priv.audit.privacy_rating;
      document.getElementById("auditKScore").innerText = `${Math.round(priv.audit.k_anonymity.protected_student_ratio * 100)}% Protected`;
      document.getElementById("auditUniqueness").innerText = `${(priv.audit.quasi_identifier_uniqueness_score * 100).toFixed(1)}% Unique Combos`;

      // Differential Privacy Sample Preview
      const dpBox = document.getElementById("dpPreviewBox");
      const dp = priv.differential_privacy_preview;
      dpBox.innerHTML = `
        <div class="flex justify-between text-slate-700 dark:text-slate-300">
          <span>Cohort Count (Laplace Noisy):</span>
          <span class="text-cyan-600 dark:text-cyan-400 font-bold">${dp.total_students} STUs</span>
        </div>
        <div class="flex justify-between text-slate-700 dark:text-slate-300">
          <span>Chronic Count (DP Sanitized):</span>
          <span class="text-rose-600 dark:text-rose-400 font-bold">${dp.chronic_absenteeism_count} STUs</span>
        </div>
        <div class="flex justify-between text-slate-700 dark:text-slate-300">
          <span>Mean Attendance (DP ε=1.0):</span>
          <span class="text-emerald-600 dark:text-emerald-400 font-bold">${(dp.average_attendance_rate * 100).toFixed(1)}%</span>
        </div>
        <div class="flex justify-between text-slate-700 dark:text-slate-300">
          <span>Mean Daily LMS Time (DP):</span>
          <span class="text-cyan-600 dark:text-cyan-400 font-bold">${dp.average_daily_lms_minutes} mins</span>
        </div>
      `;
    }

    if (fidRes.ok) {
      const fid = await fidRes.json();
      document.getElementById("fidelityScoreBadge").innerText = `SQS: ${fid.synthetic_quality_score}/100`;

      // KS Tests
      document.getElementById("ksAttStatus").innerText = fid.ks_tests.attendance_rate.passed
        ? `Passed (KS Stat: ${fid.ks_tests.attendance_rate.statistic})`
        : `KS Stat: ${fid.ks_tests.attendance_rate.statistic}`;

      document.getElementById("ksLmsStatus").innerText = fid.ks_tests.lms_active_minutes.passed
        ? `Passed (KS Stat: ${fid.ks_tests.lms_active_minutes.statistic})`
        : `KS Stat: ${fid.ks_tests.lms_active_minutes.statistic}`;

      document.getElementById("jsdStatus").innerText = `JSD: ${fid.jensen_shannon_divergence.attendance_distribution_jsd}`;

      // Correlation Matrix Table
      const cTable = document.getElementById("corrMatrixTable");
      cTable.innerHTML = "";
      const feats = ["Attn", "LMS", "Subm", "Quiz"];

      // Header row
      let headerTr = `<tr><th class="p-1.5 text-slate-500 bg-slate-100 dark:bg-slate-950"></th>`;
      feats.forEach(f => { headerTr += `<th class="p-1.5 text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-950">${f}</th>`; });
      headerTr += `</tr>`;
      cTable.innerHTML += headerTr;

      // Matrix rows
      fid.correlations.matrix.forEach((row, idx) => {
        let tr = `<tr><th class="p-1.5 text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-950 text-left">${feats[idx]}</th>`;
        row.forEach(val => {
          const isDiag = Math.abs(val - 1.0) < 0.01;
          const colorClass = isDiag
            ? 'text-slate-400 dark:text-slate-500 font-normal'
            : (val > 0.4 ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-700 dark:text-slate-300');
          tr += `<td class="p-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 ${colorClass}">${val.toFixed(2)}</td>`;
        });
        tr += `</tr>`;
        cTable.innerHTML += tr;
      });
    }
  } catch (err) {
    console.error("Privacy/fidelity audit load error:", err);
  }
}

// ==========================================
// WHAT-IF POLICY SIMULATION
// ==========================================

async function runPolicySimulation() {
  const policyName = document.getElementById("simPolicySelect").value;
  const intensity = parseFloat(document.getElementById("simIntensity").value);

  try {
    const res = await fetch("/api/simulate/policy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policy_name: policyName, intervention_intensity: intensity }),
    });
    if (!res.ok) return;
    const sim = await res.json();

    const card = document.getElementById("policyResultCard");
    card.classList.remove("hidden");

    document.getElementById("simBaseRate").innerText = (sim.baseline.chronic_absenteeism_rate * 100).toFixed(1) + "%";
    document.getElementById("simPostRate").innerText = (sim.post_intervention.chronic_absenteeism_rate * 100).toFixed(1) + "%";
    document.getElementById("simReductionPct").innerText = `-${sim.relative_chronic_reduction_pct}%`;
    document.getElementById("simSavedCount").innerText = `${sim.students_saved_from_chronic_absenteeism} STUs`;
  } catch (err) {
    console.error("Policy simulation error:", err);
  }
}

// ==========================================
// GENERATOR CONTROLS & PRESET APPLICATION
// ==========================================

function applyPreset(presetName) {
  if (presetName === "standard_district") {
    document.getElementById("genStudents").value = 250;
    document.getElementById("genStudentsVal").innerText = "250";
    document.getElementById("arch_consistent").value = 45;
    document.getElementById("arch_gradual").value = 20;
    document.getElementById("arch_sporadic").value = 15;
    document.getElementById("arch_slumper").value = 8;
    document.getElementById("arch_chronic").value = 7;
    document.getElementById("arch_responder").value = 5;
  } else if (presetName === "urban_at_risk") {
    document.getElementById("genStudents").value = 300;
    document.getElementById("genStudentsVal").innerText = "300";
    document.getElementById("arch_consistent").value = 25;
    document.getElementById("arch_gradual").value = 30;
    document.getElementById("arch_sporadic").value = 20;
    document.getElementById("arch_slumper").value = 10;
    document.getElementById("arch_chronic").value = 10;
    document.getElementById("arch_responder").value = 5;
  } else if (presetName === "hybrid_academy") {
    document.getElementById("genStudents").value = 250;
    document.getElementById("genStudentsVal").innerText = "250";
    document.getElementById("arch_consistent").value = 40;
    document.getElementById("arch_gradual").value = 25;
    document.getElementById("arch_sporadic").value = 15;
    document.getElementById("arch_slumper").value = 10;
    document.getElementById("arch_chronic").value = 5;
    document.getElementById("arch_responder").value = 5;
  }
}

async function runGeneration() {
  const btn = document.getElementById("btnGenerate");
  const origText = btn.innerHTML;
  btn.innerHTML = `<span class="flex items-center space-x-2"><svg class="animate-spin h-4 w-4 text-slate-900" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg><span>Synthesizing & Saving to SQLite...</span></span>`;
  btn.disabled = true;

  const numStudents = parseInt(document.getElementById("genStudents").value);
  const totalWeeks = parseInt(document.getElementById("genWeeks").value);
  const seed = parseInt(document.getElementById("genSeed").value);
  const district = document.getElementById("genDistrict").value;
  const enableDp = document.getElementById("dpNoiseToggle").checked;

  const weights = {
    CONSISTENT_ACHIEVER: parseFloat(document.getElementById("arch_consistent").value),
    GRADUAL_DISENGAGER: parseFloat(document.getElementById("arch_gradual").value),
    SPORADIC_ATTENDEE: parseFloat(document.getElementById("arch_sporadic").value),
    LATE_SEMESTER_SLUMPER: parseFloat(document.getElementById("arch_slumper").value),
    CHRONIC_ABSENTEE: parseFloat(document.getElementById("arch_chronic").value),
    INTERVENTION_RESPONDER: parseFloat(document.getElementById("arch_responder").value),
  };

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        num_students: numStudents,
        total_weeks: totalWeeks,
        random_seed: seed,
        district_name: district,
        archetype_weights: weights,
        enable_dp_noise: enableDp,
        dp_epsilon: 1.0,
      }),
    });

    if (!res.ok) {
      alert("Error generating cohort.");
      return;
    }

    // Refresh entire app state from SQLite database
    await initDashboard();
    switchTab("overview");
  } catch (err) {
    console.error("Generation error:", err);
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
}
