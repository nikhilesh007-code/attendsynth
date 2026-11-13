"""Unit tests for FastAPI endpoints and business logic."""

import unittest
from attendsynth.api.app import (
    app,
    startup_event,
    health_check,
    get_presets,
    get_current_cohort_summary,
    get_students,
    get_student_detail,
    predict_student_risk,
    simulate_policy,
    export_data,
    PredictRiskRequest,
    PolicySimRequest,
)


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        startup_event()

    def test_health_check(self):
        res = health_check()
        self.assertEqual(res["status"], "healthy")
        self.assertTrue(res["cohort_loaded"])

    def test_presets(self):
        presets = get_presets()
        self.assertGreaterEqual(len(presets), 3)
        self.assertEqual(presets[0]["id"], "standard_district")

    def test_cohort_summary_and_students(self):
        summary = get_current_cohort_summary()
        self.assertIn("summary", summary)
        self.assertGreater(summary["summary"]["total_students"], 0)

        # Test student listing
        students_res = get_students(page=1, limit=10, search=None, risk_level="ALL", archetype="ALL")
        self.assertIn("students", students_res)
        self.assertLessEqual(len(students_res["students"]), 10)

        # Test single student detail
        first_stu_id = students_res["students"][0]["student_id"]
        detail = get_student_detail(first_stu_id)
        self.assertEqual(detail["student"]["student_id"], first_stu_id)
        self.assertGreater(len(detail["daily_timeline"]), 0)

    def test_model_inference_endpoint(self):
        req = PredictRiskRequest(
            early_attendance_rate=0.85,
            early_tardy_rate=0.12,
            early_unexcused_rate=0.05,
            early_avg_daily_lms_minutes=30.0,
            early_lms_trend_decay=0.20,
            early_submission_rate=0.80,
            early_quiz_average=70.0,
            baseline_gpa=2.9,
        )
        res = predict_student_risk(req)
        self.assertIn("predicted_risk_tier", res)
        self.assertIn("predicted_risk_probability", res)
        self.assertIn("recommended_action", res)

    def test_policy_simulation_endpoint(self):
        req = PolicySimRequest(
            policy_name="counselor_case_management",
            intervention_intensity=0.5,
        )
        res = simulate_policy(req)
        self.assertIn("relative_chronic_reduction_pct", res)
        self.assertGreaterEqual(res["students_saved_from_chronic_absenteeism"], 0)

    def test_export_endpoints(self):
        res_csv = export_data("students_csv")
        self.assertEqual(res_csv.media_type, "text/csv")
        self.assertIn(b"student_id", res_csv.body)

        res_edfi = export_data("edfi_json")
        self.assertEqual(res_edfi.media_type, "application/json")
        self.assertIn(b"Ed-Fi-Data-Standard", res_edfi.body)


if __name__ == "__main__":
    unittest.main()
