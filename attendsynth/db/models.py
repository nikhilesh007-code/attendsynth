"""SQLAlchemy relational models for persistent cohort, student, and telemetry storage."""

import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from attendsynth.db.database import Base


class CohortModel(Base):
    __tablename__ = "cohorts"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    district_name = Column(String(128), nullable=False)
    num_students = Column(Integer, nullable=False)
    total_weeks = Column(Integer, nullable=False)
    random_seed = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=False, index=True)
    summary_json = Column(Text, nullable=False)
    config_json = Column(Text, nullable=False)

    students = relationship("StudentModel", back_populates="cohort", cascade="all, delete-orphan")
    daily_records = relationship("DailyRecordModel", back_populates="cohort", cascade="all, delete-orphan")
    trained_models = relationship("MLModelRecord", back_populates="cohort", cascade="all, delete-orphan")


class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cohort_id = Column(String(64), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(32), nullable=False, index=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    display_name = Column(String(128), nullable=False)
    school_name = Column(String(128), nullable=False, index=True)
    grade_level = Column(Integer, nullable=False, index=True)
    archetype = Column(String(64), nullable=False, index=True)
    archetype_label = Column(String(128), nullable=False)
    baseline_gpa = Column(Float, nullable=False)
    socioeconomic_tier = Column(String(64), nullable=False)
    counselor_code = Column(String(32), nullable=False)
    
    # Aggregated Longitudinal KPIs
    total_instructional_days = Column(Integer, default=80)
    days_present = Column(Integer, default=0)
    days_tardy = Column(Integer, default=0)
    unexcused_absences = Column(Integer, default=0)
    excused_absences = Column(Integer, default=0)
    attendance_rate = Column(Float, nullable=False, index=True)
    absence_rate = Column(Float, nullable=False)
    chronic_absenteeism_flag = Column(Boolean, nullable=False, index=True)
    total_lms_minutes = Column(Float, default=0.0)
    avg_daily_lms_minutes = Column(Float, default=0.0)
    assignments_due = Column(Integer, default=0)
    assignments_submitted = Column(Integer, default=0)
    assignment_submission_rate = Column(Float, default=0.0)
    assignment_ontime_rate = Column(Float, default=0.0)
    average_quiz_score = Column(Float, default=0.0)
    composite_risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(32), nullable=False, index=True)
    early_warning_trigger_day = Column(Integer, nullable=True)
    early_warning_trigger_week = Column(Integer, nullable=True)
    recommended_intervention = Column(String(64), nullable=False)

    cohort = relationship("CohortModel", back_populates="students")

    __table_args__ = (
        Index("ix_students_cohort_risk", "cohort_id", "risk_level"),
        Index("ix_students_cohort_arch", "cohort_id", "archetype"),
    )


class DailyRecordModel(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cohort_id = Column(String(64), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(32), nullable=False, index=True)
    date = Column(String(16), nullable=False)
    day_index = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False, index=True)
    weekday = Column(Integer, nullable=False)
    attendance_status = Column(String(32), nullable=False)
    lms_active_minutes = Column(Float, nullable=False)
    lms_logins = Column(Integer, default=0)
    assignment_due = Column(Boolean, default=False)
    submission_status = Column(String(32), nullable=True)
    quiz_given = Column(Boolean, default=False)
    quiz_score = Column(Float, nullable=True)
    daily_engagement_score = Column(Float, nullable=False)

    cohort = relationship("CohortModel", back_populates="daily_records")

    __table_args__ = (
        Index("ix_daily_cohort_student", "cohort_id", "student_id"),
        Index("ix_daily_cohort_day", "cohort_id", "day_index"),
    )


class MLModelRecord(Base):
    __tablename__ = "trained_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cohort_id = Column(String(64), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True)
    model_type = Column(String(64), nullable=False)
    observation_weeks = Column(Integer, nullable=False)
    roc_auc = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    metrics_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cohort = relationship("CohortModel", back_populates="trained_models")
