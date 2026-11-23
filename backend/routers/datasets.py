"""
Datasets & Cohorts Router for AttendSynth AI.
Handles generation, retrieval, activation, renaming, deletion, comparison, and multi-format exports
with full institutional linkages and longitudinal weekly engagement data.
"""

import io
import json
import uuid
import datetime
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    DatasetModel,
    StudentModel,
    WeeklyLogModel,
    InstitutionModel,
    DepartmentModel,
    CourseModel,
    CohortCourseModel,
)
from ..schemas import DatasetCreateRequest, DatasetRenameRequest, DatasetResponse
from ..services.data_generator import SyntheticDataGenerator, DEFAULT_COURSES

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _dataset_to_response(ds: DatasetModel, db: Optional[Session] = None) -> DatasetResponse:
    courses = json.loads(ds.courses_json) if ds.courses_json else DEFAULT_COURSES
    inst_name = None
    dept_name = None

    if db and ds.institution_id:
        inst = db.query(InstitutionModel).filter(InstitutionModel.id == ds.institution_id).first()
        if inst:
            inst_name = inst.name
    if db and ds.department_id:
        dept = db.query(DepartmentModel).filter(DepartmentModel.id == ds.department_id).first()
        if dept:
            dept_name = dept.name

    return DatasetResponse(
        id=ds.id,
        name=ds.name,
        institution_id=ds.institution_id,
        institution_name=inst_name,
        department_id=ds.department_id,
        department_name=dept_name,
        academic_year=ds.academic_year or "2026-2027",
        created_at=ds.created_at,
        num_students=ds.num_students,
        num_weeks=ds.num_weeks,
        semester=ds.semester,
        profile=ds.profile,
        courses=courses,
        random_seed=ds.random_seed,
        is_active=bool(ds.is_active),
        mean_attendance=round(ds.mean_attendance or 0.0, 1),
        mean_engagement=round(ds.mean_engagement or 0.0, 1),
        mean_marks=round(ds.mean_marks or 0.0, 1),
        mean_assignment_completion=round(ds.mean_assignment_completion or 0.0, 1),
        high_risk_count=ds.high_risk_count or 0,
        medium_risk_count=ds.medium_risk_count or 0,
        low_risk_count=ds.low_risk_count or 0,
    )


def get_active_dataset(db: Session) -> Optional[DatasetModel]:
    active = db.query(DatasetModel).filter(DatasetModel.is_active == True).first()
    if not active:
        active = db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).first()
    return active


@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    institution_id: Optional[str] = None,
    department_id: Optional[str] = None,
):
    """List all saved cohorts in SQLite with optional institutional filtering."""
    query = db.query(DatasetModel)
    if institution_id:
        query = query.filter(DatasetModel.institution_id == institution_id)
    if department_id:
        query = query.filter(DatasetModel.department_id == department_id)

    datasets = query.order_by(DatasetModel.created_at.desc()).all()
    return [_dataset_to_response(ds, db) for ds in datasets]


@router.get("/active", response_model=DatasetResponse)
def get_active(db: Session = Depends(get_db)):
    """Get the currently active cohort."""
    active = get_active_dataset(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active cohort found.")
    return _dataset_to_response(active, db)


@router.post("/generate", response_model=DatasetResponse)
def generate_dataset(req: DatasetCreateRequest, db: Session = Depends(get_db)):
    """Generates a new synthetic student cohort and saves to SQLite."""
    dataset_id = f"ds_{uuid.uuid4().hex[:8]}"

    # Resolve course list and course objects from DB or request
    courses_to_use = []
    course_catalog = []
    selected_course_models = []

    if req.course_ids and len(req.course_ids) > 0:
        db_courses = db.query(CourseModel).filter(CourseModel.id.in_(req.course_ids)).all()
        for c in db_courses:
            courses_to_use.append(f"{c.code}: {c.name}")
            course_catalog.append({"id": c.id, "code": c.code, "name": c.name})
            selected_course_models.append(c)

    if not courses_to_use:
        if req.courses and len(req.courses) > 0:
            courses_to_use = req.courses
        else:
            courses_to_use = DEFAULT_COURSES

    default_name = req.name or f"Cohort {req.semester} - {req.population_profile} ({req.num_students} STUs)"

    generator = SyntheticDataGenerator(seed=req.random_seed)
    students_df, weekly_df = generator.generate_cohort(
        num_students=req.num_students,
        num_weeks=req.num_weeks,
        courses=courses_to_use,
        semester=req.semester,
        academic_year=req.academic_year,
        population_profile=req.population_profile,
        institution_id=req.institution_id,
        department_id=req.department_id,
        cohort_id=dataset_id,
        course_catalog=course_catalog,
    )

    # Deactivate existing active datasets
    db.query(DatasetModel).update({DatasetModel.is_active: False})

    # Summary metrics
    mean_att = float(students_df["attendance_pct"].mean())
    mean_eng = float(students_df["engagement_score"].mean())
    mean_marks = float(students_df["avg_marks"].mean())
    mean_assign = float(students_df["assignment_completion_pct"].mean())
    high_cnt = int((students_df["risk_level"] == "High").sum())
    med_cnt = int((students_df["risk_level"] == "Medium").sum())
    low_cnt = int((students_df["risk_level"] == "Low").sum())

    dataset_record = DatasetModel(
        id=dataset_id,
        name=default_name,
        institution_id=req.institution_id,
        department_id=req.department_id,
        academic_year=req.academic_year,
        num_students=req.num_students,
        num_weeks=req.num_weeks,
        semester=req.semester,
        profile=req.population_profile,
        courses_json=json.dumps(courses_to_use),
        random_seed=req.random_seed,
        is_active=True,
        mean_attendance=mean_att,
        mean_engagement=mean_eng,
        mean_marks=mean_marks,
        mean_assignment_completion=mean_assign,
        high_risk_count=high_cnt,
        medium_risk_count=med_cnt,
        low_risk_count=low_cnt,
    )
    db.add(dataset_record)

    # Associate courses in junction table
    for c in selected_course_models:
        db.add(CohortCourseModel(cohort_id=dataset_id, course_id=c.id))

    # Insert students
    student_models = []
    for _, row in students_df.iterrows():
        student_models.append(
            StudentModel(
                student_id=row["student_id"],
                dataset_id=dataset_id,
                institution_id=req.institution_id,
                course_id=row.get("course_id"),
                name=row["name"],
                course=row["course"],
                semester=row["semester"],
                academic_year=row["academic_year"],
                attendance_pct=float(row["attendance_pct"]),
                lms_logins_per_week=float(row["lms_logins_per_week"]),
                participation_score=float(row["participation_score"]),
                assignment_completion_pct=float(row["assignment_completion_pct"]),
                avg_marks=float(row["avg_marks"]),
                late_submissions=int(row["late_submissions"]),
                engagement_score=float(row["engagement_score"]),
                engagement_level=str(row["engagement_level"]),
                risk_score=float(row["risk_score"]),
                risk_level=str(row["risk_level"]),
                weekly_trajectory=str(row["weekly_trajectory"]),
                flagged_reasons_json=json.dumps(row["flagged_reasons"]),
                risk_breakdown_json=json.dumps(row.get("risk_breakdown", {})),
                support_recommendation=str(row["support_recommendation"]),
                weekly_history_json=json.dumps(row["weekly_history"]),
            )
        )
    db.bulk_save_objects(student_models)

    # Insert weekly logs
    weekly_models = []
    for _, row in weekly_df.iterrows():
        weekly_models.append(
            WeeklyLogModel(
                dataset_id=dataset_id,
                student_id=row["student_id"],
                course_id=row.get("course_id"),
                week_number=int(row["week_number"]),
                engagement_score=float(row["engagement_score"]),
                attendance_pct=float(row["attendance_pct"]),
                lms_active_minutes=float(row["lms_active_minutes"]),
                participation_score=float(row.get("participation_score", 0.0)),
                assignments_completed=int(row["assignments_completed"]),
                marks=float(row.get("marks", 0.0)),
            )
        )
    db.bulk_save_objects(weekly_models)
    db.commit()

    return _dataset_to_response(dataset_record, db)


@router.post("/{dataset_id}/activate", response_model=DatasetResponse)
def activate_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Sets a dataset as the active cohort for all analytics."""
    target = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    db.query(DatasetModel).update({DatasetModel.is_active: False})
    target.is_active = True
    db.commit()
    db.refresh(target)
    return _dataset_to_response(target, db)


@router.patch("/{dataset_id}/rename", response_model=DatasetResponse)
def rename_dataset(dataset_id: str, req: DatasetRenameRequest, db: Session = Depends(get_db)):
    """Renames an existing dataset."""
    target = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    target.name = req.name.strip()
    db.commit()
    db.refresh(target)
    return _dataset_to_response(target, db)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Deletes a dataset and cascades to its students, weekly logs, and ML runs."""
    target = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    was_active = target.is_active
    db.delete(target)
    db.commit()

    if was_active:
        next_active = db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).first()
        if next_active:
            next_active.is_active = True
            db.commit()

    return {"message": f"Dataset {dataset_id} deleted successfully."}


@router.get("/{dataset_id}/export/{export_format}")
def export_dataset(dataset_id: str, export_format: str, db: Session = Depends(get_db)):
    """
    Exports dataset in CSV, Excel, or JSON format.
    Includes both student summary records and longitudinal weekly engagement history.
    """
    target = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    students = db.query(StudentModel).filter(StudentModel.dataset_id == dataset_id).all()
    weekly_logs = db.query(WeeklyLogModel).filter(WeeklyLogModel.dataset_id == dataset_id).order_by(WeeklyLogModel.student_id, WeeklyLogModel.week_number).all()

    student_rows = []
    for s in students:
        student_rows.append({
            "student_id": s.id,
            "name": s.name,
            "institution_id": s.institution_id or "",
            "course": s.course,
            "semester": s.semester,
            "academic_year": s.academic_year or "",
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
    students_df = pd.DataFrame(student_rows)

    weekly_rows = []
    for w in weekly_logs:
        weekly_rows.append({
            "student_id": w.student_id,
            "week_number": w.week_number,
            "attendance_pct": w.attendance_pct,
            "lms_active_minutes": w.lms_active_minutes,
            "participation_score": w.participation_score,
            "assignments_completed": w.assignments_completed,
            "marks": w.marks,
            "engagement_score": w.engagement_score,
        })
    weekly_df = pd.DataFrame(weekly_rows)

    clean_name = target.name.replace(" ", "_").replace(":", "").replace("/", "_")
    fmt = export_format.lower()

    if fmt == "csv":
        output = io.StringIO()
        students_df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=AttendSynth_{clean_name}_students.csv"},
        )
    elif fmt == "weekly_csv":
        output = io.StringIO()
        weekly_df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=AttendSynth_{clean_name}_weekly_history.csv"},
        )
    elif fmt in ["xlsx", "excel"]:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            students_df.to_excel(writer, sheet_name="Students", index=False)
            weekly_df.to_excel(writer, sheet_name="Weekly_Engagement", index=False)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=AttendSynth_{clean_name}_comprehensive.xlsx"},
        )
    elif fmt == "json":
        json_obj = {
            "cohort": _dataset_to_response(target, db).dict(),
            "students": student_rows,
            "weekly_engagement": weekly_rows,
        }
        json_str = json.dumps(json_obj, indent=2, default=str)
        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=AttendSynth_{clean_name}_full.json"},
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Supported: csv, weekly_csv, excel, json.")


@router.get("/compare")
def compare_datasets(id1: str = Query(...), id2: str = Query(...), db: Session = Depends(get_db)):
    """Compares two cohorts side-by-side."""
    d1 = db.query(DatasetModel).filter(DatasetModel.id == id1).first()
    d2 = db.query(DatasetModel).filter(DatasetModel.id == id2).first()
    if not d1 or not d2:
        raise HTTPException(status_code=404, detail="One or both datasets not found.")

    return {
        "dataset_1": _dataset_to_response(d1, db),
        "dataset_2": _dataset_to_response(d2, db),
        "deltas": {
            "attendance_diff": round(d2.mean_attendance - d1.mean_attendance, 1),
            "engagement_diff": round(d2.mean_engagement - d1.mean_engagement, 1),
            "high_risk_diff": d2.high_risk_count - d1.high_risk_count,
        },
    }
