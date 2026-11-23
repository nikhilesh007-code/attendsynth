"""
Pydantic Schemas for AttendSynth AI API validation.
Supports Institutions, Departments, Courses, Cohorts, Students, and EWS Analytics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# -------------------------------------------------------------
# Institution Schemas
# -------------------------------------------------------------
class InstitutionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    type: str = Field(default="University", max_length=64)
    location: str = Field(default="", max_length=255)
    description: str = Field(default="")


class InstitutionUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    type: Optional[str] = Field(None, max_length=64)
    location: Optional[str] = None
    description: Optional[str] = None


class InstitutionResponse(BaseModel):
    id: str
    name: str
    type: str
    location: str
    description: str
    created_at: datetime
    departments_count: int = 0
    cohorts_count: int = 0

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Department Schemas
# -------------------------------------------------------------
class DepartmentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    institution_id: str = Field(..., min_length=1, max_length=64)


class DepartmentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    institution_id: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: str
    name: str
    institution_id: str
    institution_name: Optional[str] = None
    created_at: datetime
    courses_count: int = 0

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Course Schemas
# -------------------------------------------------------------
class CourseCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=255)
    department_id: Optional[str] = None
    semester: str = Field(default="Semester 1", max_length=64)
    credits: int = Field(default=3, ge=1, le=10)
    description: str = Field(default="")


class CourseUpdateRequest(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=32)
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    department_id: Optional[str] = None
    semester: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = None


class CourseResponse(BaseModel):
    id: str
    code: str
    name: str
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    semester: str
    credits: int
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Cohort / Dataset Schemas
# -------------------------------------------------------------
class DatasetCreateRequest(BaseModel):
    name: Optional[str] = None
    institution_id: Optional[str] = None
    department_id: Optional[str] = None
    academic_year: str = "2026-2027"
    semester: str = "Fall 2026"
    num_students: int = Field(default=250, ge=1, le=5000)
    num_weeks: int = Field(default=16, ge=4, le=32)
    courses: Optional[List[str]] = None
    course_ids: Optional[List[str]] = None
    population_profile: str = "Balanced engagement"
    random_seed: int = 42


class DatasetRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class DatasetResponse(BaseModel):
    id: str
    name: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    academic_year: str = "2026-2027"
    created_at: datetime
    num_students: int
    num_weeks: int
    semester: str
    profile: str
    courses: List[str]
    random_seed: int
    is_active: bool
    mean_attendance: float
    mean_engagement: float
    mean_marks: float
    mean_assignment_completion: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Student Schemas
# -------------------------------------------------------------
class StudentResponse(BaseModel):
    id: str
    student_id: str
    dataset_id: str
    institution_id: Optional[str] = None
    course_id: Optional[str] = None
    name: str
    course: str
    semester: str
    academic_year: str = "2026-2027"
    attendance_pct: float
    lms_logins_per_week: float
    participation_score: float
    assignment_completion_pct: float
    avg_marks: float
    late_submissions: int
    engagement_score: float
    engagement_level: str
    risk_score: float
    risk_level: str
    weekly_trajectory: str
    flagged_reasons: List[str]
    risk_breakdown: Dict[str, float] = Field(default_factory=dict)
    support_recommendation: str
    weekly_history: List[float]

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    students: List[StudentResponse]


class WeeklyLogResponse(BaseModel):
    id: int
    dataset_id: str
    student_id: str
    course_id: Optional[str] = None
    week_number: int
    attendance_pct: float
    lms_active_minutes: float
    participation_score: float
    assignments_completed: int
    marks: float
    engagement_score: float

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Early Warning System Schemas
# -------------------------------------------------------------
class EarlyWarningFlaggedStudent(BaseModel):
    id: str
    name: str
    course: str
    attendance_pct: float
    participation_score: float
    assignment_completion_pct: float
    late_submissions: int
    risk_score: float
    risk_level: str
    flagged_reasons: List[str]
    support_recommendation: str


class EarlyWarningSummaryResponse(BaseModel):
    total_students: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    flagged_students: List[EarlyWarningFlaggedStudent]
    reasons_breakdown: Dict[str, int]
    mtss_recommendations: Dict[str, List[str]]


# -------------------------------------------------------------
# AI Schemas
# -------------------------------------------------------------
class AIQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    model: Optional[str] = None
    dataset_id: Optional[str] = None


class AIInsightResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    success: bool
    status: str
    response: str
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    is_fallback: bool = False
    error: Optional[str] = None
    retry_after: Optional[str] = None


class AITestConnectionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    success: bool
    status: str
    message: str
    model: Optional[str] = None
    latency_ms: Optional[float] = None
    retry_after: Optional[str] = None


# -------------------------------------------------------------
# Telemetry, Simulation & ML Schemas
# -------------------------------------------------------------
class AnalyticsScopesResponse(BaseModel):
    active_cohort_id: str
    active_cohort_name: str
    active_cohort_students: int
    saved_cohorts_count: int
    total_students_across_all_cohorts: int


class SimulationRequest(BaseModel):
    attendance_shift: float = Field(default=0.0, ge=-30.0, le=30.0)
    participation_shift: float = Field(default=0.0, ge=-30.0, le=30.0)
    assignment_shift: float = Field(default=0.0, ge=-30.0, le=30.0)
    lms_shift: float = Field(default=0.0, ge=-50.0, le=50.0)


class SimulationResult(BaseModel):
    baseline_mean_attendance: float
    simulated_mean_attendance: float
    baseline_mean_engagement: float
    simulated_mean_engagement: float
    baseline_high_risk: int
    simulated_high_risk: int
    rescued_from_high_risk: int
    baseline_risk_distribution: Dict[str, int]
    simulated_risk_distribution: Dict[str, int]
    baseline_engagement_distribution: Dict[str, int]
    simulated_engagement_distribution: Dict[str, int]


class MLTrainRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_type: str = "Random Forest"  # or "Decision Tree"
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    random_seed: int = 42


class MLTrainResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_type: str
    test_size: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: Dict[str, int]
    feature_importances: Dict[str, float]
    sample_size: int
    disclaimer: str
