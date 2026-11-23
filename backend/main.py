"""
AttendSynth AI - Production FastAPI Main Application.
"""

import os
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

# Load root .env or local .env
env_paths = [Path(__file__).resolve().parent / ".env", Path(__file__).resolve().parent.parent / ".env"]
for p in env_paths:
    if p.exists():
        load_dotenv(p)

from .database import engine, Base, SessionLocal, get_db
from .models import (
    DatasetModel,
    StudentModel,
    WeeklyLogModel,
    InstitutionModel,
    DepartmentModel,
    CourseModel,
    CohortCourseModel,
)
from .services.data_generator import SyntheticDataGenerator, DEFAULT_COURSES
from .routers import (
    datasets,
    students,
    analytics,
    early_warning,
    ai,
    institutions,
    departments,
    courses,
)


def _migrate_sqlite_schema(db: Session):
    """Safely adds missing columns to SQLite tables if upgrading an existing database."""
    migrations = [
        ("datasets", "institution_id", "VARCHAR(64)"),
        ("datasets", "department_id", "VARCHAR(64)"),
        ("datasets", "academic_year", "VARCHAR(32) DEFAULT '2026-2027'"),
        ("students", "institution_id", "VARCHAR(64)"),
        ("students", "course_id", "VARCHAR(64)"),
        ("students", "academic_year", "VARCHAR(32) DEFAULT '2026-2027'"),
        ("weekly_logs", "course_id", "VARCHAR(64)"),
        ("weekly_logs", "marks", "FLOAT DEFAULT 0.0"),
        ("weekly_logs", "participation_score", "FLOAT DEFAULT 0.0"),
    ]
    for table, col, col_type in migrations:
        try:
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
            db.commit()
        except Exception:
            # Column already exists
            db.rollback()


def seed_institutions_and_courses(db: Session):
    """Seeds default sample institutions, departments, and course records."""
    inst_count = db.query(InstitutionModel).count()
    if inst_count == 0:
        print("Seeding sample academic institutions and departments...")
        srm = InstitutionModel(
            id="INST_SRM",
            name="SRM Institute of Science and Technology",
            type="University",
            location="Kattankulathur, Chennai, India",
            description="Leading private multi-stream research university with top computing and engineering schools.",
        )
        horizon = InstitutionModel(
            id="INST_HORIZON",
            name="Horizon Metro Public University",
            type="Public University",
            location="Metro District, USA",
            description="Comprehensive public university offering accredited science, technology, and engineering degrees.",
        )
        db.add_all([srm, horizon])
        db.commit()

        # Departments
        dept_cse = DepartmentModel(
            id="DEPT_SRM_CSE",
            name="Department of Computer Science & Engineering",
            institution_id="INST_SRM",
        )
        dept_ds = DepartmentModel(
            id="DEPT_SRM_DS",
            name="Department of Data Science & Artificial Intelligence",
            institution_id="INST_SRM",
        )
        dept_ece = DepartmentModel(
            id="DEPT_SRM_ECE",
            name="Department of Electronics & Communication",
            institution_id="INST_SRM",
        )
        dept_hm = DepartmentModel(
            id="DEPT_HM_CS",
            name="School of Computing & Informatics",
            institution_id="INST_HORIZON",
        )
        db.add_all([dept_cse, dept_ds, dept_ece, dept_hm])
        db.commit()

    # Seed Courses
    course_count = db.query(CourseModel).count()
    if course_count == 0:
        print("Seeding sample academic courses...")
        sample_courses = [
            CourseModel(
                id="CRS_CS101",
                code="CS101",
                name="Programming Fundamentals",
                department_id="DEPT_SRM_CSE",
                semester="Semester 1",
                credits=4,
                description="Introductory C/Python programming, control flow, functions, and memory structures.",
            ),
            CourseModel(
                id="CRS_DS201",
                code="DS201",
                name="Data Science",
                department_id="DEPT_SRM_DS",
                semester="Semester 3",
                credits=3,
                description="Exploratory data analysis, statistical inferencing, regression, and data visualization.",
            ),
            CourseModel(
                id="CRS_AI301",
                code="AI301",
                name="Artificial Intelligence",
                department_id="DEPT_SRM_DS",
                semester="Semester 5",
                credits=4,
                description="Search algorithms, heuristic evaluation, knowledge graphs, and neural architectures.",
            ),
            CourseModel(
                id="CRS_DBMS202",
                code="DBMS202",
                name="Database Management Systems",
                department_id="DEPT_SRM_CSE",
                semester="Semester 3",
                credits=3,
                description="Relational calculus, SQL querying, schema normalization, and transaction ACID properties.",
            ),
            CourseModel(
                id="CRS_OS203",
                code="OS203",
                name="Operating Systems",
                department_id="DEPT_SRM_CSE",
                semester="Semester 4",
                credits=4,
                description="Process concurrency, memory paging, deadlocks, and virtual filesystem architectures.",
            ),
            CourseModel(
                id="CRS_JAVA204",
                code="JAVA204",
                name="Object-Oriented Programming",
                department_id="DEPT_SRM_CSE",
                semester="Semester 2",
                credits=3,
                description="Java polymorphism, design patterns, encapsulation, exceptions, and event-driven interfaces.",
            ),
        ]
        db.add_all(sample_courses)
        db.commit()


def init_database():
    """Initializes tables and seeds initial benchmark cohort if SQLite is empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _migrate_sqlite_schema(db)
        seed_institutions_and_courses(db)

        count = db.query(DatasetModel).count()
        if count == 0:
            print("Seeding initial benchmark cohort (250 students)...")
            ds_id = f"ds_seed_{uuid.uuid4().hex[:6]}"
            courses_list = [
                "CS101: Programming Fundamentals",
                "DS201: Data Science",
                "AI301: Artificial Intelligence",
                "DBMS202: Database Management Systems",
                "OS203: Operating Systems",
                "JAVA204: Object-Oriented Programming",
            ]
            gen = SyntheticDataGenerator(seed=42)
            students_df, weekly_df = gen.generate_cohort(
                num_students=250,
                num_weeks=16,
                courses=courses_list,
                semester="Fall 2026",
                academic_year="2026-2027",
                population_profile="Balanced engagement",
                institution_id="INST_SRM",
                department_id="DEPT_SRM_CSE",
                cohort_id=ds_id,
            )
            mean_att = float(students_df["attendance_pct"].mean())
            mean_eng = float(students_df["engagement_score"].mean())
            mean_marks = float(students_df["avg_marks"].mean())
            mean_assign = float(students_df["assignment_completion_pct"].mean())
            high_cnt = int((students_df["risk_level"] == "High").sum())
            med_cnt = int((students_df["risk_level"] == "Medium").sum())
            low_cnt = int((students_df["risk_level"] == "Low").sum())

            dataset = DatasetModel(
                id=ds_id,
                name="SRM University - CSE Cohort 2026-27 (250 STUs)",
                institution_id="INST_SRM",
                department_id="DEPT_SRM_CSE",
                academic_year="2026-2027",
                num_students=250,
                num_weeks=16,
                semester="Fall 2026",
                profile="Balanced engagement",
                courses_json=json.dumps(courses_list),
                random_seed=42,
                is_active=True,
                mean_attendance=mean_att,
                mean_engagement=mean_eng,
                mean_marks=mean_marks,
                mean_assignment_completion=mean_assign,
                high_risk_count=high_cnt,
                medium_risk_count=med_cnt,
                low_risk_count=low_cnt,
            )
            db.add(dataset)

            # Insert students
            s_objs = []
            for _, r in students_df.iterrows():
                s_objs.append(
                    StudentModel(
                        student_id=r["student_id"],
                        dataset_id=ds_id,
                        institution_id="INST_SRM",
                        name=r["name"],
                        course=r["course"],
                        semester=r["semester"],
                        academic_year="2026-2027",
                        attendance_pct=float(r["attendance_pct"]),
                        lms_logins_per_week=float(r["lms_logins_per_week"]),
                        participation_score=float(r["participation_score"]),
                        assignment_completion_pct=float(r["assignment_completion_pct"]),
                        avg_marks=float(r["avg_marks"]),
                        late_submissions=int(r["late_submissions"]),
                        engagement_score=float(r["engagement_score"]),
                        engagement_level=str(r["engagement_level"]),
                        risk_score=float(r["risk_score"]),
                        risk_level=str(r["risk_level"]),
                        weekly_trajectory=str(r["weekly_trajectory"]),
                        flagged_reasons_json=json.dumps(r["flagged_reasons"]),
                        risk_breakdown_json=json.dumps(r.get("risk_breakdown", {})),
                        support_recommendation=str(r["support_recommendation"]),
                        weekly_history_json=json.dumps(r["weekly_history"]),
                    )
                )
            db.bulk_save_objects(s_objs)

            # Insert weekly logs
            w_objs = []
            for _, r in weekly_df.iterrows():
                w_objs.append(
                    WeeklyLogModel(
                        dataset_id=ds_id,
                        student_id=r["student_id"],
                        week_number=int(r["week_number"]),
                        engagement_score=float(r["engagement_score"]),
                        attendance_pct=float(r["attendance_pct"]),
                        lms_active_minutes=float(r["lms_active_minutes"]),
                        participation_score=float(r.get("participation_score", 0.0)),
                        assignments_completed=int(r["assignments_completed"]),
                        marks=float(r.get("marks", 0.0)),
                    )
                )
            db.bulk_save_objects(w_objs)
            db.commit()
            print(f"Successfully seeded benchmark cohort {ds_id} with 250 students and {len(w_objs)} weekly records.")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="AttendSynth AI API",
    description="Production Synthetic Student Engagement & Academic Early Warning Backend",
    version="2.1.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(institutions.router, prefix="/api")
app.include_router(departments.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
# Alias /api/cohorts to datasets router for clean domain parity
app.include_router(datasets.router, prefix="/api/cohorts")
app.include_router(students.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(early_warning.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint indicating backend, actual SQLite connectivity, and Groq status."""
    db_connected = False
    db_error = None
    try:
        # Actually execute a live database query to verify SQLite connection
        db.execute(text("SELECT 1")).scalar()
        db_connected = True
    except Exception as e:
        db_connected = False
        db_error = str(e)

    has_groq = bool(os.getenv("GROQ_API_KEY"))
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    return {
        "status": "online" if db_connected else "degraded",
        "service": "AttendSynth AI Backend",
        "version": "2.1.0",
        "db_connected": db_connected,
        "db_dialect": "sqlite",
        "db_error": db_error,
        "groq_configured": has_groq,
        "groq_model": groq_model,
        "groq_status": "API Key Configured" if has_groq else "API Key Missing",
    }
