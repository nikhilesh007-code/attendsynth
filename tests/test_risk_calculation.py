"""
Unit Tests for AttendSynth AI Risk Engine, Synthetic Identities, and Multi-Factor Deficits.
Validates:
1. Strict mathematical bounds (0 <= risk_score <= 100).
2. Elimination of artificial 100.0 clamping on non-extreme low attendance.
3. Indicator breakdown summation to composite risk score.
4. Monotonicity: worsening individual metrics cannot decrease risk.
5. Unique, stable student_id generation and non-colliding duplicate display names.
"""

import unittest
import sys
import os

# Ensure backend is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from services.risk_engine import EarlyWarningEngine
from services.data_generator import DataGenerator


class TestRiskEngine(unittest.TestCase):
    def test_risk_score_bounds_and_extremes(self):
        """Test that risk scores are strictly bounded between 0.0 and 100.0 at all extremes."""
        # Perfect student: zero deficits across all indicators
        perfect = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=100.0,
            assignment_completion_pct=100.0,
            avg_marks=100.0,
            participation_score=100.0,
            late_submissions=0,
            weekly_trajectory="Improving",
        )
        self.assertEqual(perfect["risk_score"], 0.0)
        self.assertEqual(perfect["risk_level"], "Low")
        self.assertEqual(len(perfect["flagged_reasons"]), 0)

        # Worst-case struggling student
        worst = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=0.0,
            assignment_completion_pct=0.0,
            avg_marks=0.0,
            participation_score=0.0,
            late_submissions=10,
            weekly_trajectory="Declining",
            lms_logins_per_week=0.0,
        )
        self.assertLessEqual(worst["risk_score"], 100.0)
        self.assertGreaterEqual(worst["risk_score"], 90.0)
        self.assertEqual(worst["risk_level"], "High")

    def test_low_attendance_alone_does_not_clamp_to_100(self):
        """
        Verify that a student with low attendance (e.g. 50%) who still submits assignments
        and participates is NOT falsely clamped to 100.0.
        """
        result = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=50.0,
            assignment_completion_pct=85.0,
            avg_marks=75.0,
            participation_score=75.0,
            late_submissions=0,
            weekly_trajectory="Stable",
        )
        # Attendance deficit: (85 - 50) / 60 * 30 = 17.5 pts
        # Other deficits = 0
        self.assertLess(result["risk_score"], 40.0)
        self.assertGreater(result["risk_score"], 10.0)
        self.assertNotEqual(result["risk_score"], 100.0)

    def test_indicator_breakdown_sums_to_composite_score(self):
        """Ensure the sum of all 5 indicator breakdown components equals the composite risk score."""
        test_cases = [
            (72.0, 68.0, 62.0, 55.0, 2, "Declining"),
            (45.0, 50.0, 48.0, 40.0, 5, "Declining"),
            (88.0, 92.0, 80.0, 85.0, 0, "Improving"),
            (60.0, 70.0, 55.0, 60.0, 3, "Stable"),
        ]

        for att, assign, marks, part, late, traj in test_cases:
            res = EarlyWarningEngine.calculate_student_risk(
                attendance_pct=att,
                assignment_completion_pct=assign,
                avg_marks=marks,
                participation_score=part,
                late_submissions=late,
                weekly_trajectory=traj,
            )
            bd = res["indicator_breakdown"]
            component_sum = round(
                bd["attendance_deficit"]
                + bd["assignment_deficit"]
                + bd["marks_deficit"]
                + bd["participation_deficit"]
                + bd["behavior_penalty"],
                1,
            )
            self.assertAlmostEqual(res["risk_score"], component_sum, delta=0.01)

    def test_monotonicity_worsening_metrics_increase_risk(self):
        """Ensure that lowering performance on any metric monotonically increases or keeps risk constant."""
        baseline = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=80.0,
            assignment_completion_pct=80.0,
            avg_marks=70.0,
            participation_score=70.0,
            late_submissions=1,
            weekly_trajectory="Stable",
        )

        worse_attendance = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=60.0,
            assignment_completion_pct=80.0,
            avg_marks=70.0,
            participation_score=70.0,
            late_submissions=1,
            weekly_trajectory="Stable",
        )
        self.assertGreater(worse_attendance["risk_score"], baseline["risk_score"])

        worse_assignments = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=80.0,
            assignment_completion_pct=50.0,
            avg_marks=70.0,
            participation_score=70.0,
            late_submissions=1,
            weekly_trajectory="Stable",
        )
        self.assertGreater(worse_assignments["risk_score"], baseline["risk_score"])

        declining_trajectory = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=80.0,
            assignment_completion_pct=80.0,
            avg_marks=70.0,
            participation_score=70.0,
            late_submissions=1,
            weekly_trajectory="Declining",
        )
        self.assertGreater(declining_trajectory["risk_score"], baseline["risk_score"])

    def test_threshold_flag_accuracy(self):
        """Verify that trigger flags correspond accurately to institutional thresholds."""
        res = EarlyWarningEngine.calculate_student_risk(
            attendance_pct=55.0,  # < 60% trigger
            assignment_completion_pct=45.0,  # < 50% trigger
            avg_marks=75.0,  # >= 50% no trigger
            participation_score=35.0,  # < 40 trigger
            late_submissions=5,  # >= 4 trigger
            weekly_trajectory="Declining",  # trigger
        )
        flags = res["flagged_reasons"]
        self.assertTrue(any("Attendance critically low" in f for f in flags))
        self.assertTrue(any("Assignment completion lagging" in f for f in flags))
        self.assertFalse(any("Formative marks below passing" in f for f in flags))
        self.assertTrue(any("In-class participation deficient" in f for f in flags))
        self.assertTrue(any("Chronic late submissions" in f for f in flags))
        self.assertTrue(any("decay pattern" in f for f in flags))


class TestSyntheticIdentityIntegrity(unittest.TestCase):
    def test_unique_stable_student_ids(self):
        """Verify generated cohort has 100% unique student_ids with the canonical SYNTH-STU prefix."""
        generator = DataGenerator(seed=42)
        df, _ = generator.generate_cohort(num_students=100, num_weeks=8)

        student_ids = df["student_id"].tolist()
        self.assertEqual(len(student_ids), 100)
        self.assertEqual(len(set(student_ids)), 100, "All student_ids in cohort must be unique")
        for sid in student_ids:
            self.assertTrue(sid.startswith("SYNTH-STU-"), f"student_id {sid} must have standard prefix")

    def test_duplicate_display_names_maintain_unique_identities(self):
        """
        Verify that if two synthetic students happen to share the same display name,
        their student_ids and records remain completely separate and non-colliding.
        """
        generator = DataGenerator(seed=123)
        df, _ = generator.generate_cohort(num_students=50, num_weeks=4)

        # Force two students to have the same display name
        df.loc[0, "name"] = "Jordan Rivera"
        df.loc[1, "name"] = "Jordan Rivera"

        # student_id must still be unique
        self.assertNotEqual(df.loc[0, "student_id"], df.loc[1, "student_id"])

        # Longitudinal weekly histories should remain independent
        self.assertIsNotNone(df.loc[0, "weekly_history"])
        self.assertIsNotNone(df.loc[1, "weekly_history"])

    def test_no_clamped_100_in_generated_cohort(self):
        """Verify that in a generated cohort, no students are artificially clamped to 100.0."""
        generator = DataGenerator(seed=999)
        df, _ = generator.generate_cohort(num_students=200, num_weeks=12)

        clamped_100 = (df["risk_score"] == 100.0).sum()
        self.assertEqual(clamped_100, 0, "No students should have risk clamped to 100.0")

        # Max risk should be realistic (e.g. 60 - 85)
        max_risk = df["risk_score"].max()
        self.assertLess(max_risk, 95.0, f"Max risk should not be unrealistically high, got {max_risk}")


if __name__ == "__main__":
    unittest.main()
