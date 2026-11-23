"""
SQLAlchemy ORM Models for AttendSynth AI.
Supports dynamic Institutions, Departments, Courses, Cohorts, Students, and Weekly Logs.
"""

import datetime
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, synonym
from .database import Base


class InstitutionModel(Base):
    __tablename__ = "institutions"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(64), default="University")  # University, College, K-12 District, EdTech Academy
    location = Column(String(255), default="")
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    departments = relationship("DepartmentModel", back_populates="institution", cascade="all, delete-orphan")
    cohorts = relationship("DatasetModel", back_populates="institution")
    students = relationship("StudentModel", back_populates="institution")


class DepartmentModel(Base):
    __tablename__ = "departments"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    institution_id = Column(String(64), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    institution = relationship("InstitutionModel", back_populates="departments")
    courses = relationship("CourseModel", back_populates="department", cascade="all, delete-orphan")
    cohorts = relationship("DatasetModel", back_populates="department")


class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(String(64), primary_key=True, index=True)
    code = Column(String(32), nullable=False, index=True)  # e.g., CS101, DS201
    name = Column(String(255), nullable=False)
    department_id = Column(String(64), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    semester = Column(String(64), default="Semester 1")
    credits = Column(Integer, default=3)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    department = relationship("DepartmentModel", back_populates="courses")
    students = relationship("StudentModel", back_populates="assigned_course_rel")


class CohortCourseModel(Base):
    __tablename__ = "cohort_courses"

    cohort_id = Column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(String(64), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)


class DatasetModel(Base):
    """Represents an academic Cohort and its longitudinal dataset."""
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    institution_id = Column(String(64), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(64), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year = Column(String(32), default="2026-2027")
    semester = Column(String(64), default="Fall 2026")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    num_students = Column(Integer, default=250)
    num_weeks = Column(Integer, default=16)
    profile = Column(String(64), default="Balanced engagement")
    courses_json = Column(Text, default="[]")
    random_seed = Column(Integer, default=42)
    is_active = Column(Boolean, default=True)

    # Cached high-level summary KPIs for fast dashboard load
    mean_attendance = Column(Float, default=0.0)
    mean_engagement = Column(Float, default=0.0)
    mean_marks = Column(Float, default=0.0)
    mean_assignment_completion = Column(Float, default=0.0)
    high_risk_count = Column(Integer, default=0)
    medium_risk_count = Column(Integer, default=0)
    low_risk_count = Column(Integer, default=0)

    institution = relationship("InstitutionModel", back_populates="cohorts")
    department = relationship("DepartmentModel", back_populates="cohorts")
    students = relationship("StudentModel", back_populates="dataset", cascade="all, delete-orphan")
    weekly_logs = relationship("WeeklyLogModel", back_populates="dataset", cascade="all, delete-orphan")
    ml_runs = relationship("MLRunModel", back_populates="dataset", cascade="all, delete-orphan")


class StudentModel(Base):
    __tablename__ = "students"

    # Unique, stable, primary key student_id
    student_id = Column(String(64), primary_key=True, index=True)
    id = synonym("student_id")

    dataset_id = Column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    institution_id = Column(String(64), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(String(64), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    course = Column(String(128), nullable=False, index=True)
    semester = Column(String(64), default="Fall 2026")
    academic_year = Column(String(32), default="2026-2027")
    attendance_pct = Column(Float, default=0.0)
    lms_logins_per_week = Column(Float, default=0.0)
    participation_score = Column(Float, default=0.0)
    assignment_completion_pct = Column(Float, default=0.0)
    avg_marks = Column(Float, default=0.0)
    late_submissions = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    engagement_level = Column(String(32), default="Medium", index=True)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(32), default="Low", index=True)
    weekly_trajectory = Column(String(32), default="Stable")
    flagged_reasons_json = Column(Text, default="[]")
    risk_breakdown_json = Column(Text, default="{}")
    support_recommendation = Column(Text, default="")
    weekly_history_json = Column(Text, default="[]")

    dataset = relationship("DatasetModel", back_populates="students")
    institution = relationship("InstitutionModel", back_populates="students")
    assigned_course_rel = relationship("CourseModel", back_populates="students")
    weekly_logs = relationship("WeeklyLogModel", back_populates="student", cascade="all, delete-orphan")


class WeeklyLogModel(Base):
    __tablename__ = "weekly_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    student_id = Column(String(64), ForeignKey("students.student_id", ondelete="CASCADE"), index=True)
    course_id = Column(String(64), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    week_number = Column(Integer, nullable=False)
    engagement_score = Column(Float, default=0.0)
    attendance_pct = Column(Float, default=0.0)
    lms_active_minutes = Column(Float, default=0.0)
    participation_score = Column(Float, default=0.0)
    assignments_completed = Column(Integer, default=0)
    marks = Column(Float, default=0.0)

    dataset = relationship("DatasetModel", back_populates="weekly_logs")
    student = relationship("StudentModel", back_populates="weekly_logs")


class MLRunModel(Base):
    __tablename__ = "ml_runs"

    id = Column(String(64), primary_key=True, index=True)
    dataset_id = Column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model_type = Column(String(64), nullable=False)
    test_size = Column(Float, default=0.2)
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    confusion_matrix_json = Column(Text, default="{}")
    feature_importances_json = Column(Text, default="{}")
    metrics_json = Column(Text, default="{}")

    dataset = relationship("DatasetModel", back_populates="ml_runs")
