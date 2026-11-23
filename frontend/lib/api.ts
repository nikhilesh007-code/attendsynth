import {
  Dataset,
  Student,
  StudentListResponse,
  CohortKPIs,
  CohortDistributions,
  WeeklyTrend,
  EarlyWarningSummary,
  SimulationResult,
  MLTrainResponse,
  AIInsightResponse,
  AITestConnectionResponse,
  AnalyticsScopes,
  Institution,
  Department,
  Course,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    let errorMsg = `API request failed with status ${res.status}`;
    if (typeof errorBody.detail === "string") {
      errorMsg = errorBody.detail;
    } else if (Array.isArray(errorBody.detail)) {
      errorMsg = errorBody.detail
        .map((e: any) => (typeof e === "object" && e?.msg ? `${e.loc?.slice(-1)[0] || "field"}: ${e.msg}` : String(e)))
        .join("; ");
    } else if (typeof errorBody.detail === "object" && errorBody.detail !== null) {
      errorMsg = JSON.stringify(errorBody.detail);
    }
    throw new Error(errorMsg);
  }

  return res.json();
}

export const api = {
  // Institutions
  getInstitutions: (params?: { search?: string; type_filter?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.type_filter) q.set("type_filter", params.type_filter);
    return fetchApi<Institution[]>(`/institutions?${q.toString()}`);
  },
  getInstitution: (id: string) => fetchApi<Institution>(`/institutions/${id}`),
  createInstitution: (data: { name: string; type?: string; location?: string; description?: string }) =>
    fetchApi<Institution>("/institutions", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateInstitution: (
    id: string,
    data: { name?: string; type?: string; location?: string; description?: string }
  ) =>
    fetchApi<Institution>(`/institutions/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteInstitution: (id: string) =>
    fetchApi<{ message: string }>(`/institutions/${id}`, { method: "DELETE" }),
  getInstitutionDepartments: (id: string) =>
    fetchApi<Department[]>(`/institutions/${id}/departments`),

  // Departments
  getDepartments: (params?: { institution_id?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.institution_id) q.set("institution_id", params.institution_id);
    if (params?.search) q.set("search", params.search);
    return fetchApi<Department[]>(`/departments?${q.toString()}`);
  },
  getDepartment: (id: string) => fetchApi<Department>(`/departments/${id}`),
  createDepartment: (data: { name: string; institution_id: string }) =>
    fetchApi<Department>("/departments", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateDepartment: (id: string, data: { name?: string; institution_id?: string }) =>
    fetchApi<Department>(`/departments/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteDepartment: (id: string) =>
    fetchApi<{ message: string }>(`/departments/${id}`, { method: "DELETE" }),
  getDepartmentCourses: (id: string) =>
    fetchApi<Course[]>(`/departments/${id}/courses`),

  // Courses
  getCourses: (params?: { department_id?: string; semester?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.department_id) q.set("department_id", params.department_id);
    if (params?.semester) q.set("semester", params.semester);
    if (params?.search) q.set("search", params.search);
    return fetchApi<Course[]>(`/courses?${q.toString()}`);
  },
  getCourse: (id: string) => fetchApi<Course>(`/courses/${id}`),
  createCourse: (data: {
    code: string;
    name: string;
    department_id?: string;
    semester?: string;
    credits?: number;
    description?: string;
  }) =>
    fetchApi<Course>("/courses", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateCourse: (
    id: string,
    data: {
      code?: string;
      name?: string;
      department_id?: string;
      semester?: string;
      credits?: number;
      description?: string;
    }
  ) =>
    fetchApi<Course>(`/courses/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteCourse: (id: string) =>
    fetchApi<{ message: string }>(`/courses/${id}`, { method: "DELETE" }),

  // Datasets / Cohorts
  getDatasets: (params?: { institution_id?: string; department_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.institution_id) q.set("institution_id", params.institution_id);
    if (params?.department_id) q.set("department_id", params.department_id);
    return fetchApi<Dataset[]>(`/datasets?${q.toString()}`);
  },
  getActiveDataset: () => fetchApi<Dataset>("/datasets/active"),
  generateDataset: (payload: {
    name?: string;
    institution_id?: string;
    department_id?: string;
    academic_year?: string;
    num_students: number;
    num_weeks: number;
    courses?: string[];
    course_ids?: string[];
    semester?: string;
    population_profile?: string;
    random_seed?: number;
  }) =>
    fetchApi<Dataset>("/datasets/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  activateDataset: (id: string) =>
    fetchApi<Dataset>(`/datasets/${id}/activate`, { method: "POST" }),
  renameDataset: (id: string, name: string) =>
    fetchApi<Dataset>(`/datasets/${id}/rename`, {
      method: "PATCH",
      body: JSON.stringify({ name }),
    }),
  deleteDataset: (id: string) =>
    fetchApi<{ message: string }>(`/datasets/${id}`, { method: "DELETE" }),
  compareDatasets: (id1: string, id2: string) =>
    fetchApi<any>(`/datasets/compare?id1=${id1}&id2=${id2}`),

  // Analytics
  getKPIs: (datasetId?: string) =>
    fetchApi<CohortKPIs>(`/analytics/kpis${datasetId ? `?dataset_id=${datasetId}` : ""}`),
  getScopes: () => fetchApi<AnalyticsScopes>("/analytics/scopes"),
  getDistributions: (datasetId?: string) =>
    fetchApi<CohortDistributions>(
      `/analytics/distributions${datasetId ? `?dataset_id=${datasetId}` : ""}`
    ),
  getWeeklyTrends: (datasetId?: string) =>
    fetchApi<WeeklyTrend[]>(
      `/analytics/weekly-trends${datasetId ? `?dataset_id=${datasetId}` : ""}`
    ),

  // Students
  getStudents: (params: {
    datasetId?: string;
    search?: string;
    course?: string;
    riskLevel?: string;
    engagementLevel?: string;
    sortBy?: string;
    sortOrder?: string;
    page?: number;
    pageSize?: number;
  }) => {
    const q = new URLSearchParams();
    if (params.datasetId) q.set("dataset_id", params.datasetId);
    if (params.search) q.set("search", params.search);
    if (params.course) q.set("course", params.course);
    if (params.riskLevel) q.set("risk_level", params.riskLevel);
    if (params.engagementLevel) q.set("engagement_level", params.engagementLevel);
    if (params.sortBy) q.set("sort_by", params.sortBy);
    if (params.sortOrder) q.set("sort_order", params.sortOrder);
    if (params.page) q.set("page", params.page.toString());
    if (params.pageSize) q.set("page_size", params.pageSize.toString());
    return fetchApi<StudentListResponse>(`/students?${q.toString()}`);
  },
  getStudentDetail: (studentId: string, datasetId?: string) =>
    fetchApi<Student>(
      `/students/${studentId}${datasetId ? `?dataset_id=${datasetId}` : ""}`
    ),

  // Early Warning
  getEarlyWarningSummary: (datasetId?: string) =>
    fetchApi<EarlyWarningSummary>(
      `/early-warning/summary${datasetId ? `?dataset_id=${datasetId}` : ""}`
    ),

  // AI Insights
  queryAI: (query: string, datasetId?: string, model?: string) => {
    let resolvedDatasetId = datasetId;
    let resolvedModel = model;
    // Defensive check: swap if model name was passed in datasetId position
    if (datasetId && (datasetId.includes("/") || datasetId.startsWith("llama") || datasetId.startsWith("gpt") || datasetId.startsWith("qwen"))) {
      resolvedModel = datasetId;
      resolvedDatasetId = model;
    }
    return fetchApi<AIInsightResponse>(
      `/ai/query${resolvedDatasetId ? `?dataset_id=${encodeURIComponent(resolvedDatasetId)}` : ""}`,
      {
        method: "POST",
        body: JSON.stringify({ query, model: resolvedModel, dataset_id: resolvedDatasetId }),
      }
    );
  },
  getExecutiveSummary: (datasetId?: string) =>
    fetchApi<AIInsightResponse>(
      `/ai/dataset-summary${datasetId ? `?dataset_id=${datasetId}` : ""}`
    ),
  testGroqConnection: (model?: string) =>
    fetchApi<AITestConnectionResponse>(
      `/ai/test-connection${model ? `?model=${encodeURIComponent(model)}` : ""}`,
      { method: "POST" }
    ),

  // Health
  getHealth: () =>
    fetchApi<{
      status: string;
      service: string;
      version: string;
      db_connected?: boolean;
      db_dialect?: string;
      db_error?: string | null;
      groq_configured: boolean;
      groq_model?: string;
      groq_status?: string;
    }>("/health"),
};
