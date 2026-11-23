"""
Comprehensive End-to-End Test Suite for AttendSynth AI (FastAPI + SQLite + Services).
"""

import unittest
import json
import pandas as pd
from backend.database import SessionLocal
from backend.main import init_database
from backend.routers import datasets, students, analytics, early_warning, ai
from backend.schemas import (
    DatasetCreateRequest,
    AIQueryRequest,
    DatasetRenameRequest,
)


class TestAttendSynthFullstack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_database_and_active_cohort(self):
        """Verify baseline dataset exists and has valid student records."""
        ds_list = datasets.list_datasets(self.db)
        self.assertGreaterEqual(len(ds_list), 1)
        active = datasets.get_active(self.db)
        self.assertIsNotNone(active.id)
        self.assertGreater(active.num_students, 0)
        self.assertGreater(active.mean_attendance, 50.0)

    def test_02_dataset_generation(self):
        """Verify generating a new cohort works and persists to SQLite."""
        req = DatasetCreateRequest(
            name="Test Verification Cohort",
            num_students=50,
            num_weeks=8,
            semester="Fall 2026",
            population_profile="Mostly engaged students",
            random_seed=123,
        )
        new_ds = datasets.generate_dataset(req, self.db)
        self.assertEqual(new_ds.num_students, 50)
        self.assertEqual(new_ds.num_weeks, 8)
        self.assertTrue(new_ds.is_active)
        self.assertGreater(new_ds.mean_attendance, 60.0)

    def test_03_student_analytics_and_pagination(self):
        """Verify student search, filter, and pagination."""
        res = students.list_students(page=1, page_size=10, db=self.db)
        self.assertEqual(len(res.students), 10)
        self.assertGreater(res.total, 0)

        # Test single student detail with weekly history
        first_stu_id = res.students[0].id
        detail = students.get_student_detail(first_stu_id, db=self.db)
        self.assertEqual(detail["id"], first_stu_id)
        self.assertIn("weekly_logs", detail)
        self.assertGreater(len(detail["weekly_logs"]), 0)

    def test_04_early_warning_system(self):
        """Verify early warning risk rules and MTSS recommendations."""
        ews = early_warning.get_early_warning_summary(db=self.db)
        self.assertGreater(ews.total_students, 0)
        self.assertIn("Attendance critically low (<60%)", ews.reasons_breakdown)
        self.assertIn("Tier 1 (Universal Support)", ews.mtss_recommendations)
        self.assertIn("Tier 3 (Intensive Support)", ews.mtss_recommendations)

    def test_05_analytics_kpis_and_distributions(self):
        """Verify KPI calculations and chart distribution payloads."""
        kpis = analytics.get_kpis(db=self.db)
        self.assertIn("avg_attendance", kpis)
        self.assertIn("avg_engagement", kpis)

        dist = analytics.get_distributions(db=self.db)
        self.assertIn("engagement_distribution", dist)
        self.assertIn("risk_distribution", dist)
        self.assertIn("attendance_distribution", dist)
        self.assertIn("course_breakdown", dist)

    def test_08_dataset_comparison(self):
        """Verify comparing two datasets returns deltas."""
        all_ds = datasets.list_datasets(self.db)
        if len(all_ds) >= 2:
            res = datasets.compare_datasets(all_ds[0].id, all_ds[1].id, self.db)
            self.assertIn("deltas", res)
            self.assertIn("attendance_diff", res["deltas"])


if __name__ == "__main__":
    unittest.main()
