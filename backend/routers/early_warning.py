"""
Early Warning System Router for AttendSynth AI.
Evaluates academic risk tiers, reasons breakdown, and MTSS intervention protocols.
"""

from typing import Optional
import json
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import StudentModel
from ..schemas import EarlyWarningSummaryResponse, EarlyWarningFlaggedStudent
from ..services.risk_engine import EarlyWarningEngine
from .datasets import get_active_dataset

router = APIRouter(prefix="/early-warning", tags=["early-warning"])


@router.get("", response_model=EarlyWarningSummaryResponse)
@router.get("/summary", response_model=EarlyWarningSummaryResponse)
def get_early_warning_summary(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns transparent early warning breakdown and priority flagged students."""
    if not dataset_id:
        active = get_active_dataset(db)
        if not active:
            return EarlyWarningSummaryResponse(
                total_students=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                flagged_students=[],
                reasons_breakdown={},
                mtss_recommendations={},
            )
        dataset_id = active.id

    students = db.query(StudentModel).filter(StudentModel.dataset_id == dataset_id).all()
    rows = []
    for s in students:
        reasons = json.loads(s.flagged_reasons_json) if s.flagged_reasons_json else []
        rows.append({
            "student_id": s.id,
            "name": s.name,
            "course": s.course,
            "attendance_pct": s.attendance_pct,
            "participation_score": s.participation_score,
            "assignment_completion_pct": s.assignment_completion_pct,
            "avg_marks": s.avg_marks,
            "late_submissions": s.late_submissions,
            "risk_score": s.risk_score,
            "risk_level": s.risk_level,
            "weekly_trajectory": s.weekly_trajectory,
            "flagged_reasons": reasons,
            "support_recommendation": s.support_recommendation,
        })
    df = pd.DataFrame(rows)
    result = EarlyWarningEngine.evaluate_cohort(df)

    flagged_students = [
        EarlyWarningFlaggedStudent(
            id=item["id"],
            name=item["name"],
            course=item["course"],
            attendance_pct=item["attendance_pct"],
            participation_score=item["participation_score"],
            assignment_completion_pct=item["assignment_completion_pct"],
            late_submissions=item["late_submissions"],
            risk_score=item["risk_score"],
            risk_level=item["risk_level"],
            flagged_reasons=item["flagged_reasons"],
            support_recommendation=item["support_recommendation"],
        )
        for item in result["flagged_students"]
    ]

    return EarlyWarningSummaryResponse(
        total_students=result["total_students"],
        high_risk_count=result["high_risk_count"],
        medium_risk_count=result["medium_risk_count"],
        low_risk_count=result["low_risk_count"],
        flagged_students=flagged_students,
        reasons_breakdown=result["reasons_breakdown"],
        mtss_recommendations=result["mtss_recommendations"],
    )
