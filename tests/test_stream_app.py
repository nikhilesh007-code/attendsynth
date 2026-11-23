"""
Comprehensive Automated Test Suite for AttendSynth AI Core Engine.
Tests data generation, early warning logic, ML benchmarking, scenario simulator, and Groq fallback.
"""

import unittest
import io
import pandas as pd
from core.data_generator import SyntheticDataGenerator, DEFAULT_COURSES
from core.risk_engine import EarlyWarningEngine
from core.analytics import DatasetAnalytics
from core.scenario_simulator import ScenarioSimulator
from core.ml_model import AcademicMLBenchmarker
from core.ai_insights import GroqInsightsEngine
import core.visualizations as viz


class TestAttendSynthCore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.generator = SyntheticDataGenerator(seed=42)
        cls.students_df, cls.weekly_df = cls.generator.generate_cohort(
            num_students=100,
            num_weeks=8,
            courses=DEFAULT_COURSES,
            semester="Fall 2026",
            population_profile="Balanced engagement",
        )

    def test_synthetic_data_generation_shape_and_columns(self):
        self.assertEqual(len(self.students_df), 100)
        self.assertEqual(len(self.weekly_df), 100 * 8)

        expected_cols = [
            "student_id", "name", "course", "semester", "attendance_pct",
            "lms_logins_per_week", "participation_score", "assignment_completion_pct",
            "avg_marks", "late_submissions", "engagement_score", "engagement_level",
            "risk_score", "risk_level", "weekly_trajectory", "weekly_history"
        ]
        for col in expected_cols:
            self.assertIn(col, self.students_df.columns)

        # Check bounds
        self.assertTrue((self.students_df["attendance_pct"] >= 0).all() and (self.students_df["attendance_pct"] <= 100).all())
        self.assertTrue((self.students_df["engagement_score"] >= 0).all() and (self.students_df["engagement_score"] <= 100).all())
        self.assertTrue((self.students_df["risk_score"] >= 0).all() and (self.students_df["risk_score"] <= 100).all())

    def test_statistical_correlations(self):
        # Attendance and engagement should be positively correlated
        corr_att_eng = self.students_df["attendance_pct"].corr(self.students_df["engagement_score"])
        self.assertGreater(corr_att_eng, 0.40)

        # Engagement and risk should be strongly negatively correlated
        corr_eng_risk = self.students_df["engagement_score"].corr(self.students_df["risk_score"])
        self.assertLess(corr_eng_risk, -0.60)

    def test_population_profiles(self):
        # Mostly engaged should have higher mean engagement than at-risk heavy
        gen_high = SyntheticDataGenerator(seed=10)
        df_high, _ = gen_high.generate_cohort(num_students=60, population_profile="Mostly engaged students")

        gen_risk = SyntheticDataGenerator(seed=10)
        df_risk, _ = gen_risk.generate_cohort(num_students=60, population_profile="At-risk-heavy population")

        self.assertGreater(df_high["engagement_score"].mean(), df_risk["engagement_score"].mean())
        self.assertGreater(df_risk["risk_score"].mean(), df_high["risk_score"].mean())

    def test_early_warning_engine(self):
        ews_df = EarlyWarningEngine.evaluate_cohort(self.students_df)
        self.assertIn("ews_risk_score", ews_df.columns)
        self.assertIn("flag_reasons", ews_df.columns)
        self.assertIn("suggested_actions", ews_df.columns)

        flagged = ews_df[ews_df["is_flagged"]]
        self.assertGreaterEqual(len(flagged), 0)
        for _, row in flagged.iterrows():
            self.assertGreaterEqual(len(row["suggested_actions"]), 1)

    def test_dataset_analytics(self):
        kpis = DatasetAnalytics.compute_summary_kpis(self.students_df)
        self.assertEqual(kpis["total_students"], 100)
        self.assertGreater(kpis["avg_attendance"], 0)
        self.assertGreater(kpis["avg_engagement"], 0)

        course_summary = DatasetAnalytics.get_course_breakdown(self.students_df)
        self.assertGreaterEqual(len(course_summary), 1)

        corr_matrix = DatasetAnalytics.get_correlation_matrix(self.students_df)
        self.assertFalse(corr_matrix.empty)

    def test_scenario_simulator(self):
        sim_df, summary = ScenarioSimulator.run_simulation(
            base_df=self.students_df,
            att_delta=10.0,
            part_delta=15.0,
            assign_delta=10.0,
            lms_delta=20.0,
        )
        self.assertGreaterEqual(summary["sim_avg_attendance"], summary["baseline_avg_attendance"])
        self.assertGreaterEqual(summary["sim_avg_engagement"], summary["baseline_avg_engagement"])
        self.assertLessEqual(summary["sim_high_risk_count"], summary["baseline_high_risk_count"])

    def test_ml_benchmarker(self):
        results_rf = AcademicMLBenchmarker.train_and_evaluate(self.students_df, model_type="Random Forest")
        self.assertIn("accuracy", results_rf)
        self.assertGreaterEqual(results_rf["accuracy"], 0.70)
        self.assertEqual(len(results_rf["confusion_matrix"]), 2)
        self.assertGreater(len(results_rf["feature_importances"]), 3)

        results_dt = AcademicMLBenchmarker.train_and_evaluate(self.students_df, model_type="Decision Tree")
        self.assertIn("accuracy", results_dt)
        self.assertGreaterEqual(results_dt["accuracy"], 0.70)

    def test_groq_insights_context_and_fallback(self):
        context = GroqInsightsEngine.build_aggregate_context(self.students_df)
        self.assertEqual(context["total_students"], 100)
        self.assertIn("risk_distribution", context)

        # Fallback when no key is set
        insight = GroqInsightsEngine.generate_insight(
            df=self.students_df,
            user_query="Analyze attendance drops",
            api_key=None,
        )
        self.assertFalse(insight["success"])
        self.assertEqual(insight["error"], "MISSING_API_KEY")
        self.assertIn("fallback", insight)
        self.assertIn("Heuristic Offline Mode", insight["fallback"])

    def test_visualizations_generation(self):
        fig1 = viz.plot_engagement_distribution(self.students_df)
        self.assertIsNotNone(fig1)

        fig2 = viz.plot_attendance_distribution(self.students_df)
        self.assertIsNotNone(fig2)

        fig3 = viz.plot_risk_distribution(self.students_df)
        self.assertIsNotNone(fig3)

        fig4 = viz.plot_course_comparison(self.students_df)
        self.assertIsNotNone(fig4)

        fig5 = viz.plot_weekly_trends(self.weekly_df)
        self.assertIsNotNone(fig5)

    def test_excel_export(self):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            self.students_df.to_excel(writer, sheet_name="Students", index=False)
            self.weekly_df.to_excel(writer, sheet_name="Weekly", index=False)
        self.assertGreater(len(buffer.getvalue()), 1000)


if __name__ == "__main__":
    unittest.main()
