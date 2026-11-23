"""
AI Insights Router for AttendSynth AI.
Connects with Groq API using aggregate zero-PII metrics and pedagogical prompt engineering.
Includes rate limit handling (HTTP 429), honest connection test endpoint, and local fallback.
"""

from typing import Optional
import json
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import StudentModel
from ..schemas import AIQueryRequest, AIInsightResponse, AITestConnectionResponse
from ..services.groq_service import GroqService
from .datasets import get_active_dataset

router = APIRouter(prefix="/ai", tags=["ai"])


def _load_active_df(db: Session, dataset_id: Optional[str] = None) -> pd.DataFrame:
    # Guard against model names accidentally passed as dataset_id
    if dataset_id and ("/" in dataset_id or "gpt" in dataset_id.lower() or "qwen" in dataset_id.lower() or "llama" in dataset_id.lower()):
        dataset_id = None

    if not dataset_id:
        active = get_active_dataset(db)
        if active:
            dataset_id = active.id

    students = []
    if dataset_id:
        students = db.query(StudentModel).filter(StudentModel.dataset_id == dataset_id).all()

    # Fallback to active dataset or any cohort with students if requested id had 0 students
    if not students:
        active = get_active_dataset(db)
        if active and active.id != dataset_id:
            students = db.query(StudentModel).filter(StudentModel.dataset_id == active.id).all()
        if not students:
            # Fallback to any cohort with students in DB
            sample_student = db.query(StudentModel).first()
            if sample_student:
                students = db.query(StudentModel).filter(StudentModel.dataset_id == sample_student.dataset_id).all()

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


@router.post("/test-connection", response_model=AITestConnectionResponse)
def test_groq_connection(model: Optional[str] = None):
    """
    Directly tests model inference on Groq with a minimal prompt.
    Returns honest connection status (Groq Request Successful, Groq Rate Limited, etc.).
    """
    res = GroqService.test_connection(model=model)
    return AITestConnectionResponse(
        success=res.get("success", False),
        status=res.get("status", "Groq Temporarily Unavailable"),
        message=res.get("message", ""),
        model=res.get("model"),
        latency_ms=res.get("latency_ms"),
        retry_after=str(res.get("retry_after")) if res.get("retry_after") else None,
    )


@router.post("/query", response_model=AIInsightResponse)
def query_ai(req: AIQueryRequest, dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Queries Groq AI on the active dataset's aggregate metrics."""
    target_dataset_id = dataset_id or req.dataset_id
    df = _load_active_df(db, target_dataset_id)
    if df.empty:
        raise HTTPException(status_code=400, detail="No student data available in the active cohort.")

    res = GroqService.query(df=df, user_query=req.query, model=req.model)
    return AIInsightResponse(
        success=res.get("success", False),
        status=res.get("status", "Local Fallback Active"),
        response=res.get("response", ""),
        model_used=res.get("model_used"),
        tokens_used=res.get("tokens_used"),
        is_fallback=res.get("is_fallback", False),
        error=res.get("error"),
        retry_after=str(res.get("retry_after")) if res.get("retry_after") else None,
    )


@router.get("/dataset-summary", response_model=AIInsightResponse)
def get_executive_summary(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Generates an executive AI summary of the active cohort."""
    df = _load_active_df(db, dataset_id)
    if df.empty:
        raise HTTPException(status_code=400, detail="No active cohort data available.")

    res = GroqService.query(
        df=df,
        user_query="Provide a concise 3-bullet executive snapshot of cohort health, critical vulnerabilities, and top priority action.",
    )
    return AIInsightResponse(
        success=res.get("success", False),
        status=res.get("status", "Local Fallback Active"),
        response=res.get("response", ""),
        model_used=res.get("model_used"),
        tokens_used=res.get("tokens_used"),
        is_fallback=res.get("is_fallback", False),
        error=res.get("error"),
        retry_after=str(res.get("retry_after")) if res.get("retry_after") else None,
    )
