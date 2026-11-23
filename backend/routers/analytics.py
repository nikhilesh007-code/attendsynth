"""
Analytics Router for AttendSynth AI.
Serves summary KPIs, distributions, longitudinal cohort trends,
and database scope statistics.
"""

from typing import Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import StudentModel, WeeklyLogModel, DatasetModel
from ..services.analytics_engine import AnalyticsEngine
from ..schemas import AnalyticsScopesResponse
from .datasets import get_active_dataset

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _load_cohort_df(dataset_id: str, db: Session) -> pd.DataFrame:
    students = db.query(StudentModel).filter(StudentModel.dataset_id == dataset_id).all()
    if not students:
        return pd.DataFrame()
    rows = []
    for s in students:
        rows.append({
            "student_id": s.student_id,
            "name": s.name,
            "course": s.course,
            "attendance_pct": s.attendance_pct,
            "lms_logins_per_week": s.lms_logins_per_week,
            "participation_score": s.participation_score,
            "assignment_completion_pct": s.assignment_completion_pct,
            "avg_marks": s.avg_marks,
            "late_submissions": s.late_submissions,
            "engagement_score": s.engagement_score,
            "engagement_level": s.engagement_level,
            "risk_score": s.risk_score,
            "risk_level": s.risk_level,
            "weekly_trajectory": s.weekly_trajectory,
        })
    return pd.DataFrame(rows)


@router.get("/scopes", response_model=AnalyticsScopesResponse)
def get_analytics_scopes(db: Session = Depends(get_db)):
    """
    Returns explicit telemetry clarifying active cohort scope vs all saved cohorts in the database.
    """
    active = get_active_dataset(db)
    saved_cohorts_count = db.query(DatasetModel).count()
    total_students_across_all = db.query(StudentModel).count()

    active_id = active.id if active else "None"
    active_name = active.name if active else "No Active Cohort"
    active_students = active.num_students if active else 0

    return AnalyticsScopesResponse(
        active_cohort_id=active_id,
        active_cohort_name=active_name,
        active_cohort_students=active_students,
        saved_cohorts_count=saved_cohorts_count,
        total_students_across_all_cohorts=total_students_across_all,
    )


@router.get("/kpis")
def get_kpis(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns high-level KPI cards for the active cohort."""
    if not dataset_id:
        active = get_active_dataset(db)
        if not active:
            return AnalyticsEngine.compute_summary_kpis(pd.DataFrame())
        dataset_id = active.id

    df = _load_cohort_df(dataset_id, db)
    return AnalyticsEngine.compute_summary_kpis(df)


@router.get("/distributions")
def get_distributions(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns engagement, risk, attendance, and course distribution series."""
    if not dataset_id:
        active = get_active_dataset(db)
        if not active:
            return {}
        dataset_id = active.id

    df = _load_cohort_df(dataset_id, db)
    return AnalyticsEngine.compute_distributions(df)


@router.get("/weekly-trends")
def get_weekly_trends(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns weekly trend data across the cohort."""
    if not dataset_id:
        active = get_active_dataset(db)
        if not active:
            return []
        dataset_id = active.id

    logs = db.query(WeeklyLogModel).filter(WeeklyLogModel.dataset_id == dataset_id).all()
    if not logs:
        return []

    rows = [{
        "week_number": l.week_number,
        "engagement_score": l.engagement_score,
        "attendance_pct": l.attendance_pct,
        "lms_active_minutes": l.lms_active_minutes,
    } for l in logs]
    weekly_df = pd.DataFrame(rows)
    return AnalyticsEngine.compute_weekly_trends(weekly_df)
