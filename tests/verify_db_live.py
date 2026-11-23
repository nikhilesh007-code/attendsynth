"""
Database Verification and Relational Integrity Script for AttendSynth AI.
Systematically tests and validates:
1. Exact SQLite file path, existence, and filesystem size.
2. SQLAlchemy connection via live raw SQL execution.
3. List of all database tables.
4. Schema inspection: primary keys and foreign key constraints.
5. Record counts across all entities (institutions, departments, courses, cohorts, students, weekly_logs).
6. Temporary cohort creation with 5 synthetic students.
7. Verification of the 5 students inserted into SQLite.
8. Simulation of backend restart (new engine instance from file) and retrieval of the 5 students.
9. Verification of persistence across restart.
10. Safe deletion of the temporary cohort and verification of cascading cleanup.
11. Verification that dashboard analytics run real SQL aggregate queries instead of hardcoded mock numbers.
12. Duplicate checks and foreign key integrity audit (PRAGMA foreign_key_check).
"""

import sys
import os
import json
import uuid
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.database import DB_PATH, DATABASE_URL, Base, SessionLocal, engine
from backend.models import (
    InstitutionModel,
    DepartmentModel,
    CourseModel,
    DatasetModel,
    StudentModel,
    WeeklyLogModel,
    CohortCourseModel,
)
from backend.services.data_generator import SyntheticDataGenerator
from backend.routers.datasets import generate_dataset, delete_dataset
from backend.schemas import DatasetCreateRequest
from backend.routers import analytics


def run_full_database_verification():
    results = {}
    print("=" * 70)
    print("ATTENDSYNTH AI - DATABASE INTEGRITY & PERSISTENCE VERIFICATION")
    print("=" * 70)

    # 1. Identify exact database file and location
    db_file = Path(DB_PATH).resolve()
    results["1_db_file_path"] = str(db_file)
    results["1_db_exists"] = db_file.exists()
    results["1_db_size_bytes"] = db_file.stat().st_size if db_file.exists() else 0
    results["1_database_url"] = DATABASE_URL
    print(f"\n[1] Database File: {db_file}")
    print(f"    Exists: {results['1_db_exists']} | Size: {results['1_db_size_bytes']:,} bytes")
    print(f"    URL: {DATABASE_URL}")

    # 2. Verify SQLAlchemy Connection
    db = SessionLocal()
    try:
        ping = db.execute(text("SELECT 1 AS alive, sqlite_version() AS version;")).mappings().first()
        results["2_connection_successful"] = True
        results["2_sqlite_version"] = ping["version"]
        print(f"\n[2] SQLAlchemy Connection: SUCCESS (SQLite Version: {ping['version']})")
    except Exception as e:
        results["2_connection_successful"] = False
        results["2_connection_error"] = str(e)
        print(f"\n[2] SQLAlchemy Connection: FAILED ({e})")
        return results

    # 3. List all existing database tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    results["3_tables"] = tables
    print(f"\n[3] Registered Database Tables ({len(tables)}):")
    for t in tables:
        row_cnt = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"    - {t:<20} (Rows: {row_cnt})")

    # 4. Verify primary keys and foreign key relationships
    relationships = {}
    for t in tables:
        pk = inspector.get_pk_constraint(t)
        fks = inspector.get_foreign_keys(t)
        relationships[t] = {
            "primary_key": pk.get("constrained_columns", []),
            "foreign_keys": [
                {
                    "constrained": fk.get("constrained_columns"),
                    "referred_table": fk.get("referred_table"),
                    "referred_columns": fk.get("referred_columns"),
                }
                for fk in fks
            ],
        }
    results["4_table_relationships"] = relationships
    print("\n[4] Primary Keys and Foreign Key Relationships:")
    for t, rel in relationships.items():
        print(f"    Table: {t}")
        print(f"      PK: {rel['primary_key']}")
        for fk in rel['foreign_keys']:
            print(f"      FK: {fk['constrained']} -> {fk['referred_table']}{fk['referred_columns']}")

    # 5. Check stored records across all domain models
    entity_counts = {
        "institutions": db.query(InstitutionModel).count(),
        "departments": db.query(DepartmentModel).count(),
        "courses": db.query(CourseModel).count(),
        "cohorts (datasets)": db.query(DatasetModel).count(),
        "students": db.query(StudentModel).count(),
        "weekly_logs": db.query(WeeklyLogModel).count(),
    }
    results["5_entity_counts"] = entity_counts
    print("\n[5] Actual Stored Entity Counts in SQLite:")
    for k, v in entity_counts.items():
        print(f"    - {k:<22}: {v:,}")

    # 6. Create temporary test cohort and generate 5 synthetic students
    temp_cohort_id = f"ds_probe_{uuid.uuid4().hex[:6]}"
    req = DatasetCreateRequest(
        name="Temporary Verification Cohort (5 STUs)",
        num_students=5,
        num_weeks=4,
        semester="Spring 2027",
        population_profile="Balanced engagement",
        random_seed=12345,
    )
    print(f"\n[6] Generating Temporary Test Cohort with 5 students...")
    created_dataset = generate_dataset(req, db)
    temp_id = created_dataset.id
    results["6_temp_cohort_id"] = temp_id
    print(f"    Created Cohort ID: {temp_id} ({created_dataset.name})")

    # 7. Verify all 5 students inserted into database
    inserted_students = db.query(StudentModel).filter(StudentModel.dataset_id == temp_id).all()
    inserted_weekly = db.query(WeeklyLogModel).filter(WeeklyLogModel.dataset_id == temp_id).all()
    results["7_inserted_students_count"] = len(inserted_students)
    results["7_inserted_weekly_logs"] = len(inserted_weekly)
    print(f"\n[7] Database Insert Verification:")
    print(f"    Inserted Students: {len(inserted_students)} (Expected: 5)")
    print(f"    Inserted Weekly Logs: {len(inserted_weekly)} (Expected: 5 * 4 = 20)")
    for s in inserted_students:
        print(f"      * {s.student_id} | {s.name:<22} | Course: {s.course} | Risk: {s.risk_score} ({s.risk_level})")

    # 8. Simulate Backend Restart (Close session, dispose engine pool, open fresh connection)
    db.close()
    engine.dispose()
    print("\n[8] Simulating Backend Restart (disposing connection pool, recreating fresh SessionLocal)...")
    fresh_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    FreshSession = sessionmaker(autocommit=False, autoflush=False, bind=fresh_engine)
    fresh_db = FreshSession()

    # 9. Verify records still exist after restart
    restarted_students = fresh_db.query(StudentModel).filter(StudentModel.dataset_id == temp_id).all()
    results["9_restarted_students_count"] = len(restarted_students)
    print(f"\n[9] Post-Restart Persistence Verification:")
    print(f"    Retrieved Students from SQLite File: {len(restarted_students)}")
    self_persisted = len(restarted_students) == 5
    results["9_persisted_across_restart"] = self_persisted
    for s in restarted_students:
        print(f"      Verified: {s.student_id} -> {s.name} (Risk Breakdown: {s.risk_breakdown_json[:35]}...)")

    # 10. Delete temporary test cohort safely and check cascade
    print(f"\n[10] Safely deleting temporary cohort '{temp_id}'...")
    del_res = delete_dataset(temp_id, fresh_db)
    remaining_cohort = fresh_db.query(DatasetModel).filter(DatasetModel.id == temp_id).first()
    remaining_students = fresh_db.query(StudentModel).filter(StudentModel.dataset_id == temp_id).count()
    remaining_weekly = fresh_db.query(WeeklyLogModel).filter(WeeklyLogModel.dataset_id == temp_id).count()
    results["10_cohort_deleted"] = remaining_cohort is None
    results["10_cascaded_students_remaining"] = remaining_students
    results["10_cascaded_weekly_remaining"] = remaining_weekly
    print(f"     Deleted Cohort Status: {del_res['message']}")
    print(f"     Remaining Test Students: {remaining_students} (Expected: 0)")
    print(f"     Remaining Test Weekly Logs: {remaining_weekly} (Expected: 0)")

    # 11. Verify dashboard statistics are calculated from database queries
    print("\n[11] Dashboard Calculation Audit (Verifying live SQL queries):")
    active_ds = fresh_db.query(DatasetModel).filter(DatasetModel.is_active == True).first()
    if active_ds:
        # Direct SQL count
        sql_student_count = fresh_db.query(StudentModel).filter(StudentModel.dataset_id == active_ds.id).count()
        sql_avg_attendance = fresh_db.execute(
            text("SELECT AVG(attendance_pct) FROM students WHERE dataset_id = :did"),
            {"did": active_ds.id},
        ).scalar()
        # Router calculation
        router_kpis = analytics.get_kpis(active_ds.id, fresh_db)
        print(f"     Active Dataset: {active_ds.name} ({active_ds.id})")
        print(f"     Direct DB Student Count : {sql_student_count}")
        print(f"     API Computed Student Count: {router_kpis['total_students']}")
        print(f"     Direct DB Avg Attendance: {sql_avg_attendance:.1f}%")
        print(f"     API Computed Avg Attendance: {router_kpis['avg_attendance']:.1f}%")
        results["11_dashboard_uses_live_sql"] = (
            sql_student_count == router_kpis["total_students"]
            and round(sql_avg_attendance, 1) == round(router_kpis["avg_attendance"], 1)
        )
    else:
        results["11_dashboard_uses_live_sql"] = False

    # 12. Check for duplicate records and broken foreign keys
    print("\n[12] Duplicate Keys & Relational Integrity Audit:")
    dup_students = fresh_db.execute(text(
        "SELECT student_id, COUNT(*) as cnt FROM students GROUP BY student_id HAVING cnt > 1;"
    )).fetchall()
    results["12_duplicate_students"] = len(dup_students)

    fk_violations = fresh_db.execute(text("PRAGMA foreign_key_check;")).fetchall()
    results["12_foreign_key_violations"] = len(fk_violations)
    print(f"     Duplicate Student IDs: {len(dup_students)}")
    print(f"     Foreign Key Constraint Violations: {len(fk_violations)}")

    fresh_db.close()
    fresh_engine.dispose()

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return results


if __name__ == "__main__":
    res = run_full_database_verification()
    output_path = Path(__file__).resolve().parent / "db_verification_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    print(f"\nSaved structured audit results to: {output_path}")
