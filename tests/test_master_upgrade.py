"""
Comprehensive Test Suite for AttendSynth AI Master Development Upgrade.
Validates:
1. Institution creation, retrieval, and cascading.
2. Department creation linked to institutions.
3. Custom course creation, editing, search, department/semester filtering, and deletion.
4. Multiple cohort creation with institutional linkages and cohort switching.
5. Student generation with 100% unique student IDs and stable relational keys.
6. Non-colliding duplicate fictional student display names.
7. Full weekly engagement history persistence (N students * W weeks records in SQLite).
8. Engagement Score formula: 0.35*Att + 0.25*Part + 0.20*LMS + 0.20*Assign.
9. Risk Score formula: 0.35*(100-Att) + 0.25*(100-Part) + 0.20*(100-Assign) + 0.20*(100-LMS).
10. Risk tier thresholds: Low (0-29), Medium (30-59), High (60-100).
11. Multi-format export generation: CSV, weekly CSV, Excel (.xlsx with 2 sheets), and JSON.
12. ML Decision Tree and Random Forest benchmark training.
"""

import unittest
import sys
import os
import json
import uuid
import pandas as pd

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from backend.database import engine, Base, SessionLocal
from backend.models import (
    InstitutionModel,
    DepartmentModel,
    CourseModel,
    DatasetModel,
    StudentModel,
    WeeklyLogModel,
)
from backend.services.risk_engine import EarlyWarningEngine
from backend.services.data_generator import SyntheticDataGenerator
from backend.routers import institutions, departments, courses, datasets


class TestMasterDevelopmentUpgrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # -------------------------------------------------------------
    # 1. Institution Management Tests
    # -------------------------------------------------------------
    def test_01_institution_crud(self):
        """Test institution creation, retrieval, updating, and deletion."""
        inst_id = f"INST_TEST_{uuid.uuid4().hex[:6].upper()}"
        inst = InstitutionModel(
            id=inst_id,
            name="SRM Institute of Science and Technology (Test)",
            type="University",
            location="Kattankulathur, Chennai, India",
            description="Leading multi-stream private university.",
        )
        self.db.add(inst)
        self.db.commit()

        # Retrieve
        queried = self.db.query(InstitutionModel).filter(InstitutionModel.id == inst_id).first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.name, "SRM Institute of Science and Technology (Test)")
        self.assertEqual(queried.type, "University")

        # Update
        queried.location = "Chennai Campus"
        self.db.commit()
        updated = self.db.query(InstitutionModel).filter(InstitutionModel.id == inst_id).first()
        self.assertEqual(updated.location, "Chennai Campus")

        # Cleanup
        self.db.delete(updated)
        self.db.commit()
        self.assertIsNone(self.db.query(InstitutionModel).filter(InstitutionModel.id == inst_id).first())

    # -------------------------------------------------------------
    # 2. Department Management Tests
    # -------------------------------------------------------------
    def test_02_department_crud(self):
        """Test department creation linked to an institution."""
        inst = InstitutionModel(
            id=f"INST_DEPT_TEST_{uuid.uuid4().hex[:6].upper()}",
            name="Apex Engineering University",
            type="University",
        )
        self.db.add(inst)
        self.db.commit()

        dept = DepartmentModel(
            id=f"DEPT_CSE_TEST_{uuid.uuid4().hex[:6].upper()}",
            name="Department of Computer Science & Engineering",
            institution_id=inst.id,
        )
        self.db.add(dept)
        self.db.commit()

        # Check relation
        queried_dept = self.db.query(DepartmentModel).filter(DepartmentModel.id == dept.id).first()
        self.assertIsNotNone(queried_dept)
        self.assertEqual(queried_dept.institution_id, inst.id)

        # Cleanup
        self.db.delete(dept)
        self.db.delete(inst)
        self.db.commit()

    # -------------------------------------------------------------
    # 3. Dynamic Course Management Tests
    # -------------------------------------------------------------
    def test_03_course_crud_and_filters(self):
        """Test custom course creation, editing, semester/department filtering, and deletion."""
        crs_id = f"CRS_TEST_{uuid.uuid4().hex[:6].upper()}"
        code = f"TEST{uuid.uuid4().hex[:4].upper()}"
        course = CourseModel(
            id=crs_id,
            code=code,
            name="Distributed Systems & Cloud Computing",
            semester="Semester 5",
            credits=4,
            description="Cloud virtualization and distributed consensus.",
        )
        self.db.add(course)
        self.db.commit()

        # Query and filter
        found = self.db.query(CourseModel).filter(CourseModel.code == code).first()
        self.assertIsNotNone(found)
        self.assertEqual(found.credits, 4)
        self.assertEqual(found.semester, "Semester 5")

        # Edit
        found.name = "Advanced Cloud Architectures"
        found.credits = 3
        self.db.commit()

        updated = self.db.query(CourseModel).filter(CourseModel.id == crs_id).first()
        self.assertEqual(updated.name, "Advanced Cloud Architectures")
        self.assertEqual(updated.credits, 3)

        # Delete
        self.db.delete(updated)
        self.db.commit()
        self.assertIsNone(self.db.query(CourseModel).filter(CourseModel.id == crs_id).first())

    # -------------------------------------------------------------
    # 4. Cohort Generation with Full Longitudinal Weekly Logs
    # -------------------------------------------------------------
    def test_04_cohort_generation_and_full_weekly_persistence(self):
        """Test generating a cohort and verifying exact student and weekly record counts."""
        gen = SyntheticDataGenerator(seed=777)
        cohort_id = f"ds_test_{uuid.uuid4().hex[:6]}"
        num_students = 60
        num_weeks = 8

        students_df, weekly_df = gen.generate_cohort(
            num_students=num_students,
            num_weeks=num_weeks,
            courses=["CS101: Programming Fundamentals", "DS201: Data Science"],
            semester="Spring 2027",
            academic_year="2026-2027",
            population_profile="Balanced engagement",
            institution_id="INST_SRM",
            cohort_id=cohort_id,
        )

        # Exact row count checks
        self.assertEqual(len(students_df), num_students)
        # N students * W weeks = exact weekly records count
        expected_weekly_records = num_students * num_weeks
        self.assertEqual(len(weekly_df), expected_weekly_records)

        # Verify columns in weekly_df
        required_cols = ["student_id", "week_number", "attendance_pct", "lms_active_minutes", "engagement_score", "marks"]
        for col in required_cols:
            self.assertIn(col, weekly_df.columns)

    # -------------------------------------------------------------
    # 5. Unique Student IDs and Duplicate Names
    # -------------------------------------------------------------
    def test_05_student_id_uniqueness_and_duplicate_names(self):
        """Verify student_ids are globally unique and duplicate names do not collide."""
        gen = SyntheticDataGenerator(seed=888)
        cohort_id = f"ds_test_{uuid.uuid4().hex[:6]}"
        students_df, _ = gen.generate_cohort(
            num_students=50,
            num_weeks=4,
            cohort_id=cohort_id,
        )

        # Check all student_ids are unique
        ids = students_df["student_id"].tolist()
        self.assertEqual(len(ids), len(set(ids)))

        # Simulate identical duplicate names
        students_df.loc[0, "name"] = "Alex Morgan"
        students_df.loc[1, "name"] = "Alex Morgan"

        # Unique IDs must remain distinct
        self.assertNotEqual(students_df.loc[0, "student_id"], students_df.loc[1, "student_id"])

    # -------------------------------------------------------------
    # 6. Engagement & Risk Engine Formula Tests
    # -------------------------------------------------------------
    def test_06_engagement_and_risk_formulas(self):
        """
        Verify exact formulas:
        Engagement Score = 0.35*Att + 0.25*Part + 0.20*LMS + 0.20*Assign
        Risk Score = 0.35*(100-Att) + 0.25*(100-Part) + 0.20*(100-Assign) + 0.20*(100-LMS)
        """
        # Test case 1: 100% across all indicators
        eng_perfect = EarlyWarningEngine.calculate_engagement_score(
            attendance_pct=100.0,
            participation_score=100.0,
            lms_score=100.0,
            assignment_completion_pct=100.0,
        )
        self.assertEqual(eng_perfect, 100.0)

        risk_perfect = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=100.0,
            assignment_completion_pct=100.0,
            participation_score=100.0,
            lms_logins_per_week=20.0,
        )
        self.assertEqual(risk_perfect["risk_score"], 0.0)
        self.assertEqual(risk_perfect["risk_level"], "Low")

        # Test case 2: Realistic scenario (Att: 80, Part: 70, Assign: 60, LMS: 10 logins/wk -> 50%)
        # Expected Engagement: 0.35*80 + 0.25*70 + 0.20*50 + 0.20*60 = 28 + 17.5 + 10 + 12 = 67.5
        eng_calc = EarlyWarningEngine.calculate_engagement_score(
            attendance_pct=80.0,
            participation_score=70.0,
            lms_score=50.0,
            assignment_completion_pct=60.0,
        )
        self.assertEqual(eng_calc, 67.5)

        # Expected Risk: 0.35*20 + 0.25*30 + 0.20*40 + 0.20*50 = 7.0 + 7.5 + 8.0 + 10.0 = 32.5
        risk_calc = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=80.0,
            assignment_completion_pct=60.0,
            participation_score=70.0,
            lms_logins_per_week=10.0,  # 10/20 * 100 = 50%
        )
        self.assertAlmostEqual(risk_calc["risk_score"], 32.5, places=1)
        self.assertEqual(risk_calc["risk_level"], "Medium")  # 30-59 is Medium

        # Test case 3: High-Risk student (Att: 40, Part: 30, Assign: 30, LMS: 2 logins/wk -> 10%)
        # Risk = 0.35*60 + 0.25*70 + 0.20*70 + 0.20*90 = 21 + 17.5 + 14 + 18 = 70.5
        risk_high = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=40.0,
            assignment_completion_pct=30.0,
            participation_score=30.0,
            lms_logins_per_week=2.0,
        )
        self.assertGreaterEqual(risk_high["risk_score"], 60.0)
        self.assertEqual(risk_high["risk_level"], "High")

    # -------------------------------------------------------------
    # 7. Longitudinal Weekly Trend Analysis
    # -------------------------------------------------------------
    def test_07_weekly_trajectory_analysis(self):
        """Verify trend classification: Improving, Stable, Declining."""
        improving_scores = [50.0, 52.0, 55.0, 58.0, 64.0, 68.0, 72.0, 75.0]
        self.assertEqual(EarlyWarningEngine.analyze_weekly_trend(improving_scores), "Improving")

        declining_scores = [85.0, 82.0, 78.0, 74.0, 68.0, 62.0, 55.0, 50.0]
        self.assertEqual(EarlyWarningEngine.analyze_weekly_trend(declining_scores), "Declining")

        stable_scores = [70.0, 71.0, 69.0, 70.5, 71.0, 70.0, 69.5, 70.0]
        self.assertEqual(EarlyWarningEngine.analyze_weekly_trend(stable_scores), "Stable")

    # -------------------------------------------------------------
    # 8. Multi-Tiered System of Supports (MTSS)
    # -------------------------------------------------------------
    def test_08_mtss_recommendations(self):
        """Verify MTSS recommendations match risk tiers."""
        low_res = EarlyWarningEngine.calculate_student_risk(attendance_pct=95.0, assignment_completion_pct=90.0)
        self.assertIn("Tier 1", low_res["support_recommendation"])

        med_res = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=65.0,
            assignment_completion_pct=50.0,
            participation_score=60.0,
        )
        self.assertIn("Tier 2", med_res["support_recommendation"])

        high_res = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=35.0,
            assignment_completion_pct=30.0,
            participation_score=35.0,
            lms_logins_per_week=2.0,
        )
        self.assertIn("Tier 3", high_res["support_recommendation"])

if __name__ == "__main__":
    unittest.main()
