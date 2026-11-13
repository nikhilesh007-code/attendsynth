"""Unit tests for synthetic cohort generator."""

import unittest
from attendsynth.config import CohortConfig, Presets
from attendsynth.generator import AttendSynthGenerator


class TestAttendSynthGenerator(unittest.TestCase):

    def test_default_generation(self):
        cfg = Presets.standard_district(num_students=50, seed=123)
        cfg.calendar.total_weeks = 8
        generator = AttendSynthGenerator(cfg)
        cohort = generator.generate()

        self.assertEqual(len(cohort["students"]), 50)
        self.assertIn("summary", cohort)
        self.assertIn("daily_records", cohort)

        summary = cohort["summary"]
        self.assertEqual(summary["total_students"], 50)
        self.assertGreaterEqual(summary["average_attendance_rate"], 0.70)
        self.assertLessEqual(summary["average_attendance_rate"], 1.0)
        self.assertGreaterEqual(summary["chronic_absenteeism_count"], 0)

    def test_student_attributes_validity(self):
        cfg = Presets.standard_district(num_students=30, seed=99)
        generator = AttendSynthGenerator(cfg)
        cohort = generator.generate()

        for s in cohort["students"]:
            self.assertTrue(s["student_id"].startswith("SYNTH_STU_"))
            self.assertGreaterEqual(s["attendance_rate"], 0.0)
            self.assertLessEqual(s["attendance_rate"], 1.0)
            self.assertGreaterEqual(s["composite_risk_score"], 0.0)
            self.assertLessEqual(s["composite_risk_score"], 100.0)
            self.assertIn(s["risk_level"], ["LOW", "MODERATE", "ELEVATED", "CRITICAL"])

    def test_calendar_days_count(self):
        cfg = CohortConfig(num_students=10)
        cfg.calendar.total_weeks = 12
        generator = AttendSynthGenerator(cfg)
        cohort = generator.generate()

        # 12 weeks * 5 instructional days = 60 days
        expected_days = 60
        student_records = [r for r in cohort["daily_records"] if r["student_id"] == "SYNTH_STU_1001"]
        self.assertEqual(len(student_records), expected_days)


if __name__ == "__main__":
    unittest.main()

