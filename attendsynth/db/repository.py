"""Database repository for transactional queries, inserts, and aggregations."""

import datetime
import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from attendsynth.db.models import CohortModel, StudentModel, DailyRecordModel, MLModelRecord
from attendsynth.db.database import get_db_stats_raw


class CohortRepository:
    """Manages transactional persistence and relational queries for cohorts and telemetry."""

    @staticmethod
    def save_cohort(db: Session, cohort_data: Dict[str, Any]) -> CohortModel:
        """Inserts a freshly generated synthetic cohort, its students, and daily telemetry."""
        cohort_id = cohort_data["cohort_id"]
        cfg = cohort_data.get("config", {})
        summary = cohort_data.get("summary", {})

        # Deactivate all other cohorts so this new one becomes active
        db.query(CohortModel).update({CohortModel.is_active: False})

        # Remove any existing cohort with this id if re-generating with same seed
        existing = db.query(CohortModel).filter(CohortModel.id == cohort_id).first()
        if existing:
            db.delete(existing)
            db.flush()

        # 1. Create Cohort record
        cohort_row = CohortModel(
            id=cohort_id,
            name=cohort_data.get("cohort_name", f"Cohort {cohort_id}"),
            district_name=cfg.get("district_name", "Horizon Metro Public Schools"),
            num_students=cfg.get("num_students", len(cohort_data.get("students", []))),
            total_weeks=cfg.get("total_weeks", 16),
            random_seed=cfg.get("random_seed", 42),
            created_at=datetime.datetime.utcnow(),
            is_active=True,
            summary_json=json.dumps(summary),
            config_json=json.dumps(cfg),
        )
        db.add(cohort_row)
        db.flush()

        # 2. Batch insert students
        students = cohort_data.get("students", [])
        student_rows = []
        for s in students:
            student_rows.append(
                StudentModel(
                    cohort_id=cohort_id,
                    student_id=s["student_id"],
                    first_name=s.get("first_name", "Synthetic"),
                    last_name=s.get("last_name", "Student"),
                    display_name=s["display_name"],
                    school_name=s["school_name"],
                    grade_level=s["grade_level"],
                    archetype=s["archetype"],
                    archetype_label=s.get("archetype_label", s["archetype"]),
                    baseline_gpa=float(s.get("baseline_gpa", 3.0)),
                    socioeconomic_tier=s.get("socioeconomic_tier", "TIER_1_STANDARD"),
                    counselor_code=s.get("counselor_code", "CNSLR_101"),
                    total_instructional_days=s.get("total_instructional_days", 80),
                    days_present=s.get("days_present", 0),
                    days_tardy=s.get("days_tardy", 0),
                    unexcused_absences=s.get("unexcused_absences", 0),
                    excused_absences=s.get("excused_absences", 0),
                    attendance_rate=float(s.get("attendance_rate", 0.9)),
                    absence_rate=float(s.get("absence_rate", 0.1)),
                    chronic_absenteeism_flag=bool(s.get("chronic_absenteeism_flag", False)),
                    total_lms_minutes=float(s.get("total_lms_minutes", 0.0)),
                    avg_daily_lms_minutes=float(s.get("avg_daily_lms_minutes", 0.0)),
                    assignments_due=s.get("assignments_due", 0),
                    assignments_submitted=s.get("assignments_submitted", 0),
                    assignment_submission_rate=float(s.get("assignment_submission_rate", 0.0)),
                    assignment_ontime_rate=float(s.get("assignment_ontime_rate", 0.0)),
                    average_quiz_score=float(s.get("average_quiz_score", 0.0)),
                    composite_risk_score=float(s.get("composite_risk_score", 0.0)),
                    risk_level=s.get("risk_level", "LOW"),
                    early_warning_trigger_day=s.get("early_warning_trigger_day"),
                    early_warning_trigger_week=s.get("early_warning_trigger_week"),
                    recommended_intervention=s.get("recommended_intervention", "NONE"),
                )
            )
        db.bulk_save_objects(student_rows)

        # 3. Batch insert daily records
        daily_records = cohort_data.get("daily_records", [])
        daily_rows = []
        for r in daily_records:
            daily_rows.append(
                DailyRecordModel(
                    cohort_id=cohort_id,
                    student_id=r["student_id"],
                    date=r["date"],
                    day_index=r["day_index"],
                    week_number=r["week_number"],
                    weekday=r["weekday"],
                    attendance_status=r["attendance_status"],
                    lms_active_minutes=float(r["lms_active_minutes"]),
                    lms_logins=int(r.get("lms_logins", 0)),
                    assignment_due=bool(r.get("assignment_due", False)),
                    submission_status=r.get("submission_status"),
                    quiz_given=bool(r.get("quiz_given", False)),
                    quiz_score=float(r["quiz_score"]) if r.get("quiz_score") is not None else None,
                    daily_engagement_score=float(r.get("daily_engagement_score", 50.0)),
                )
            )
        db.bulk_save_objects(daily_rows)

        db.commit()
        return cohort_row

    @staticmethod
    def list_cohorts(db: Session) -> List[Dict[str, Any]]:
        """Lists all cohorts stored in the database with their metrics."""
        rows = db.query(CohortModel).order_by(desc(CohortModel.created_at)).all()
        result = []
        for r in rows:
            try:
                summary = json.loads(r.summary_json)
            except Exception:
                summary = {}
            result.append({
                "id": r.id,
                "cohort_id": r.id,
                "name": r.name,
                "cohort_name": r.name,
                "district_name": r.district_name,
                "num_students": r.num_students,
                "student_count": r.num_students,
                "total_weeks": r.total_weeks,
                "random_seed": r.random_seed,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
                "is_active": r.is_active,
                "average_attendance_rate": summary.get("average_attendance_rate", 0.0),
                "chronic_absenteeism_rate": summary.get("chronic_absenteeism_rate", 0.0),
                "chronic_absenteeism_count": summary.get("chronic_absenteeism_count", 0),
            })
        return result

    @staticmethod
    def get_active_cohort(db: Session) -> Optional[CohortModel]:
        """Returns the currently active cohort, or the most recent one if none marked active."""
        active = db.query(CohortModel).filter(CohortModel.is_active == True).first()
        if not active:
            active = db.query(CohortModel).order_by(desc(CohortModel.created_at)).first()
            if active:
                active.is_active = True
                db.commit()
        return active

    @staticmethod
    def set_active_cohort(db: Session, cohort_id: str) -> Optional[CohortModel]:
        """Switches the active cohort in the database."""
        target = db.query(CohortModel).filter(CohortModel.id == cohort_id).first()
        if not target:
            return None
        db.query(CohortModel).update({CohortModel.is_active: False})
        target.is_active = True
        db.commit()
        return target

    @staticmethod
    def delete_cohort(db: Session, cohort_id: str) -> bool:
        """Deletes a cohort and its associated students and records."""
        target = db.query(CohortModel).filter(CohortModel.id == cohort_id).first()
        if not target:
            return False
        db.delete(target)
        db.commit()
        return True

    @staticmethod
    def query_students(
        db: Session,
        cohort_id: str,
        page: int = 1,
        limit: int = 25,
        search: Optional[str] = None,
        risk_level: Optional[str] = None,
        archetype: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """SQL query for students with filtering, search, pagination, and sorting."""
        query = db.query(StudentModel).filter(StudentModel.cohort_id == cohort_id)

        if search:
            s_term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(StudentModel.display_name).like(s_term),
                    func.lower(StudentModel.student_id).like(s_term),
                    func.lower(StudentModel.school_name).like(s_term),
                )
            )

        if risk_level and risk_level != "ALL":
            query = query.filter(StudentModel.risk_level == risk_level)

        if archetype and archetype != "ALL":
            query = query.filter(StudentModel.archetype == archetype)

        total_count = query.count()
        offset_val = (page - 1) * limit
        rows = query.order_by(StudentModel.id.asc()).offset(offset_val).limit(limit).all()

        students = []
        for r in rows:
            students.append({
                "student_id": r.student_id,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "display_name": r.display_name,
                "school_name": r.school_name,
                "grade_level": r.grade_level,
                "archetype": r.archetype,
                "archetype_label": r.archetype_label,
                "baseline_gpa": r.baseline_gpa,
                "socioeconomic_tier": r.socioeconomic_tier,
                "counselor_code": r.counselor_code,
                "attendance_rate": r.attendance_rate,
                "absence_rate": r.absence_rate,
                "chronic_absenteeism_flag": r.chronic_absenteeism_flag,
                "days_present": r.days_present,
                "days_tardy": r.days_tardy,
                "unexcused_absences": r.unexcused_absences,
                "excused_absences": r.excused_absences,
                "total_lms_minutes": r.total_lms_minutes,
                "avg_daily_lms_minutes": r.avg_daily_lms_minutes,
                "assignments_due": r.assignments_due,
                "assignments_submitted": r.assignments_submitted,
                "assignment_submission_rate": r.assignment_submission_rate,
                "assignment_ontime_rate": r.assignment_ontime_rate,
                "average_quiz_score": r.average_quiz_score,
                "composite_risk_score": r.composite_risk_score,
                "risk_level": r.risk_level,
                "early_warning_trigger_day": r.early_warning_trigger_day,
                "early_warning_trigger_week": r.early_warning_trigger_week,
                "recommended_intervention": r.recommended_intervention,
            })

        return students, total_count

    @staticmethod
    def get_student_detail(db: Session, cohort_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        """Queries single student and their ordered daily attendance logs from DB."""
        student_row = (
            db.query(StudentModel)
            .filter(StudentModel.cohort_id == cohort_id, StudentModel.student_id == student_id)
            .first()
        )
        if not student_row:
            return None

        daily_rows = (
            db.query(DailyRecordModel)
            .filter(DailyRecordModel.cohort_id == cohort_id, DailyRecordModel.student_id == student_id)
            .order_by(DailyRecordModel.day_index.asc())
            .all()
        )

        daily_timeline = []
        for d in daily_rows:
            daily_timeline.append({
                "student_id": d.student_id,
                "date": d.date,
                "day_index": d.day_index,
                "week_number": d.week_number,
                "weekday": d.weekday,
                "attendance_status": d.attendance_status,
                "lms_active_minutes": d.lms_active_minutes,
                "lms_logins": d.lms_logins,
                "assignment_due": d.assignment_due,
                "submission_status": d.submission_status,
                "quiz_given": d.quiz_given,
                "quiz_score": d.quiz_score,
                "daily_engagement_score": d.daily_engagement_score,
            })

        student_dict = {
            "student_id": student_row.student_id,
            "first_name": student_row.first_name,
            "last_name": student_row.last_name,
            "display_name": student_row.display_name,
            "school_name": student_row.school_name,
            "grade_level": student_row.grade_level,
            "archetype": student_row.archetype,
            "archetype_label": student_row.archetype_label,
            "baseline_gpa": student_row.baseline_gpa,
            "socioeconomic_tier": student_row.socioeconomic_tier,
            "attendance_rate": student_row.attendance_rate,
            "absence_rate": student_row.absence_rate,
            "chronic_absenteeism_flag": student_row.chronic_absenteeism_flag,
            "total_lms_minutes": student_row.total_lms_minutes,
            "avg_daily_lms_minutes": student_row.avg_daily_lms_minutes,
            "assignment_submission_rate": student_row.assignment_submission_rate,
            "assignment_ontime_rate": student_row.assignment_ontime_rate,
            "average_quiz_score": student_row.average_quiz_score,
            "composite_risk_score": student_row.composite_risk_score,
            "risk_level": student_row.risk_level,
            "early_warning_trigger_day": student_row.early_warning_trigger_day,
            "early_warning_trigger_week": student_row.early_warning_trigger_week,
            "recommended_intervention": student_row.recommended_intervention,
        }

        return {
            "student": student_dict,
            "daily_timeline": daily_timeline,
        }

    @staticmethod
    def get_full_cohort_payload(db: Session, cohort_id: str) -> Optional[Dict[str, Any]]:
        """Reconstructs full in-memory cohort dictionary directly from SQL records."""
        cohort_row = db.query(CohortModel).filter(CohortModel.id == cohort_id).first()
        if not cohort_row:
            return None

        summary = json.loads(cohort_row.summary_json)
        config = json.loads(cohort_row.config_json)

        students, _ = CohortRepository.query_students(db, cohort_id, page=1, limit=10000)

        # Fetch daily records
        daily_rows = (
            db.query(DailyRecordModel)
            .filter(DailyRecordModel.cohort_id == cohort_id)
            .order_by(DailyRecordModel.day_index.asc())
            .all()
        )
        daily_records = [
            {
                "student_id": d.student_id,
                "date": d.date,
                "day_index": d.day_index,
                "week_number": d.week_number,
                "weekday": d.weekday,
                "attendance_status": d.attendance_status,
                "lms_active_minutes": d.lms_active_minutes,
                "lms_logins": d.lms_logins,
                "assignment_due": d.assignment_due,
                "submission_status": d.submission_status,
                "quiz_given": d.quiz_given,
                "quiz_score": d.quiz_score,
                "daily_engagement_score": d.daily_engagement_score,
            }
            for d in daily_rows
        ]

        return {
            "cohort_id": cohort_row.id,
            "cohort_name": cohort_row.name,
            "config": config,
            "summary": summary,
            "students": students,
            "daily_records": daily_records,
        }

    @staticmethod
    def save_trained_model(db: Session, cohort_id: str, metrics: Dict[str, Any]) -> MLModelRecord:
        """Stores trained ML model evaluation into database."""
        row = MLModelRecord(
            cohort_id=cohort_id,
            model_type=metrics.get("model_type", "random_forest"),
            observation_weeks=metrics.get("observation_weeks", 6),
            roc_auc=metrics.get("roc_auc", 0.0),
            accuracy=metrics.get("accuracy", 0.0),
            precision=metrics.get("precision", 0.0),
            recall=metrics.get("recall", 0.0),
            f1_score=metrics.get("f1_score", 0.0),
            metrics_json=json.dumps(metrics),
            created_at=datetime.datetime.utcnow(),
        )
        db.add(row)
        db.commit()
        return row

    @staticmethod
    def get_latest_model(db: Session, cohort_id: str) -> Optional[Dict[str, Any]]:
        """Fetches the latest trained ML model metrics from DB."""
        row = (
            db.query(MLModelRecord)
            .filter(MLModelRecord.cohort_id == cohort_id)
            .order_by(desc(MLModelRecord.created_at))
            .first()
        )
        if not row:
            # Fallback to any latest model
            row = db.query(MLModelRecord).order_by(desc(MLModelRecord.created_at)).first()
        if not row:
            return None
        return json.loads(row.metrics_json)

    @staticmethod
    def get_database_stats(db: Session) -> Dict[str, Any]:
        """Aggregates database-wide records and file metrics."""
        raw_stats = get_db_stats_raw()
        total_cohorts = db.query(CohortModel).count()
        total_students = db.query(StudentModel).count()
        total_daily_records = db.query(DailyRecordModel).count()
        total_models = db.query(MLModelRecord).count()

        return {
            **raw_stats,
            "total_cohorts": total_cohorts,
            "total_students": total_students,
            "total_daily_records": total_daily_records,
            "total_trained_models": total_models,
            "connected": True,
        }
