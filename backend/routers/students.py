"""
Student Analytics Router for AttendSynth AI.
Provides filtering, searching, sorting, pagination, and individual student profiles
using unique stable student_id keys.
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import StudentModel, WeeklyLogModel, DatasetModel
from ..schemas import StudentListResponse, StudentResponse
from .datasets import get_active_dataset

router = APIRouter(prefix="/students", tags=["students"])


def _student_to_response(s: StudentModel) -> StudentResponse:
    reasons = json.loads(s.flagged_reasons_json) if s.flagged_reasons_json else []
    breakdown = json.loads(s.risk_breakdown_json) if getattr(s, "risk_breakdown_json", None) else {}
    history = json.loads(s.weekly_history_json) if s.weekly_history_json else []

    return StudentResponse(
        id=s.student_id,
        student_id=s.student_id,
        dataset_id=s.dataset_id,
        name=s.name,
        course=s.course,
        semester=s.semester,
        attendance_pct=round(s.attendance_pct, 1),
        lms_logins_per_week=round(s.lms_logins_per_week, 1),
        participation_score=round(s.participation_score, 1),
        assignment_completion_pct=round(s.assignment_completion_pct, 1),
        avg_marks=round(s.avg_marks, 1),
        late_submissions=s.late_submissions,
        engagement_score=round(s.engagement_score, 1),
        engagement_level=s.engagement_level,
        risk_score=round(s.risk_score, 1),
        risk_level=s.risk_level,
        weekly_trajectory=s.weekly_trajectory,
        flagged_reasons=reasons,
        risk_breakdown=breakdown,
        support_recommendation=s.support_recommendation or "",
        weekly_history=history,
    )


@router.get("", response_model=StudentListResponse)
def list_students(
    dataset_id: Optional[str] = None,
    search: Optional[str] = None,
    course: Optional[str] = None,
    risk_level: Optional[str] = None,
    engagement_level: Optional[str] = None,
    sort_by: str = "risk_score",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lists students matching criteria with sorting and pagination."""
    if not dataset_id:
        active = get_active_dataset(db)
        if not active:
            return StudentListResponse(total=0, page=page, page_size=page_size, total_pages=0, students=[])
        dataset_id = active.id

    query = db.query(StudentModel).filter(StudentModel.dataset_id == dataset_id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(StudentModel.name.ilike(term), StudentModel.student_id.ilike(term)))

    if course and course.strip():
        query = query.filter(StudentModel.course == course.strip())

    if risk_level and risk_level.strip():
        query = query.filter(StudentModel.risk_level == risk_level.strip())

    if engagement_level and engagement_level.strip():
        query = query.filter(StudentModel.engagement_level == engagement_level.strip())

    # Sorting
    sort_col = getattr(StudentModel, sort_by, StudentModel.risk_score)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    return StudentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        students=[_student_to_response(s) for s in records],
    )


@router.get("/{student_id}")
def get_student_detail(student_id: str, dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetches comprehensive student profile with weekly logs using student_id."""
    q = db.query(StudentModel).filter(StudentModel.student_id == student_id)
    if dataset_id:
        q = q.filter(StudentModel.dataset_id == dataset_id)
    student = q.first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    weekly_logs = (
        db.query(WeeklyLogModel)
        .filter(WeeklyLogModel.student_id == student_id, WeeklyLogModel.dataset_id == student.dataset_id)
        .order_by(WeeklyLogModel.week_number.asc())
        .all()
    )

    logs_data = [
        {
            "week": f"Wk {w.week_number}",
            "week_number": w.week_number,
            "engagement_score": w.engagement_score,
            "attendance_pct": w.attendance_pct,
            "lms_active_minutes": w.lms_active_minutes,
            "assignments_completed": w.assignments_completed,
        }
        for w in weekly_logs
    ]

    resp = _student_to_response(student).model_dump()
    resp["weekly_logs"] = logs_data
    return resp
