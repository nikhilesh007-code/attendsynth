export interface Institution {
  id: string;
  name: string;
  type: string;
  location: string;
  description: string;
  created_at: string;
  departments_count: number;
  cohorts_count: number;
}

export interface Department {
  id: string;
  name: string;
  institution_id: string;
  institution_name?: string;
  created_at: string;
  courses_count: number;
}

export interface Course {
  id: string;
  code: string;
  name: string;
  department_id?: string;
  department_name?: string;
  semester: string;
  credits: number;
  description: string;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  institution_id?: string;
  institution_name?: string;
  department_id?: string;
  department_name?: string;
  academic_year?: string;
  created_at: string;
  num_students: number;
  num_weeks: number;
  semester: string;
  profile: string;
  courses: string[];
  random_seed: number;
  is_active: boolean;
  mean_attendance: number;
  mean_engagement: number;
  mean_marks: number;
  mean_assignment_completion: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
}

export interface Student {
  id: string;
  student_id: string;
  dataset_id: string;
  institution_id?: string;
  course_id?: string;
  name: string;
  course: string;
  semester: string;
  academic_year?: string;
  attendance_pct: number;
  lms_logins_per_week: number;
  participation_score: number;
  assignment_completion_pct: number;
  avg_marks: number;
  late_submissions: number;
  engagement_score: number;
  engagement_level: "High" | "Medium" | "Low";
  risk_score: number;
  risk_level: "High" | "Medium" | "Low";
  weekly_trajectory: "Improving" | "Stable" | "Declining";
  flagged_reasons: string[];
  risk_breakdown?: {
    attendance_deficit?: number;
    assignment_deficit?: number;
    marks_deficit?: number;
    participation_deficit?: number;
    behavior_penalty?: number;
  };
  support_recommendation: string;
  weekly_history: number[];
  weekly_logs?: {
    week: string;
    week_number: number;
    engagement_score: number;
    attendance_pct: number;
    lms_active_minutes: number;
    assignments_completed: number;
    marks?: number;
  }[];
}

export interface WeeklyLog {
  id: number;
  dataset_id: string;
  student_id: string;
  course_id?: string;
  week_number: number;
  attendance_pct: number;
  lms_active_minutes: number;
  participation_score: number;
  assignments_completed: number;
  marks: number;
  engagement_score: number;
}

export interface StudentListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  students: Student[];
}

export interface CohortKPIs {
  total_students: number;
  avg_attendance: number;
  avg_engagement: number;
  avg_marks: number;
  avg_assignment_completion: number;
  high_engagement_count: number;
  medium_engagement_count: number;
  low_engagement_count: number;
  high_risk_count: number;
  chronic_absent_count: number;
}

export interface AnalyticsScopes {
  active_cohort_id: string;
  active_cohort_name: string;
  active_cohort_students: number;
  saved_cohorts_count: number;
  total_students_across_all_cohorts: number;
}

export interface CohortDistributions {
  engagement_distribution: { name: string; value: number; color: string }[];
  risk_distribution: { name: string; value: number; color: string }[];
  attendance_distribution: { bin: string; count: number }[];
  course_breakdown: {
    course: string;
    students: number;
    attendance: number;
    engagement: number;
    assignment_completion: number;
    avg_risk: number;
  }[];
}

export interface WeeklyTrend {
  week: string;
  week_number: number;
  avg_engagement: number;
  avg_attendance: number;
  avg_lms_minutes: number;
}

export interface EarlyWarningFlaggedStudent {
  id: string;
  name: string;
  course: string;
  attendance_pct: number;
  participation_score: number;
  assignment_completion_pct: number;
  late_submissions: number;
  risk_score: number;
  risk_level: string;
  flagged_reasons: string[];
  support_recommendation: string;
}

export interface EarlyWarningSummary {
  total_students: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  flagged_students: EarlyWarningFlaggedStudent[];
  reasons_breakdown: Record<string, number>;
  mtss_recommendations: Record<string, string[]>;
}

export interface SimulationResult {
  baseline_mean_attendance: number;
  simulated_mean_attendance: number;
  baseline_mean_engagement: number;
  simulated_mean_engagement: number;
  baseline_high_risk: number;
  simulated_high_risk: number;
  rescued_from_high_risk: number;
  baseline_risk_distribution: Record<string, number>;
  simulated_risk_distribution: Record<string, number>;
  baseline_engagement_distribution: Record<string, number>;
  simulated_engagement_distribution: Record<string, number>;
}

export interface MLTrainResponse {
  model_type: string;
  test_size: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  confusion_matrix: {
    true_negative: number;
    false_positive: number;
    false_negative: number;
    true_positive: number;
  };
  feature_importances: Record<string, number>;
  sample_size: number;
  disclaimer: string;
}

export interface AIInsightResponse {
  success: boolean;
  status: string;
  response: string;
  model_used?: string;
  tokens_used?: number;
  is_fallback: boolean;
  error?: string;
  retry_after?: string;
}

export interface AITestConnectionResponse {
  success: boolean;
  status: string;
  message: string;
  model?: string;
  latency_ms?: number;
  retry_after?: string;
}
