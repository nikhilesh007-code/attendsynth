"""Unit tests for Early Warning ML models."""

import unittest
from attendsynth.config import Presets
from attendsynth.generator import AttendSynthGenerator
from attendsynth.models.early_warning import EarlyWarningPredictor


class TestEarlyWarningPredictor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cfg = Presets.standard_district(num_students=120, seed=42)
        generator = AttendSynthGenerator(cfg)
        cls.cohort = generator.generate()

    def test_training_and_evaluation(self):
        predictor = EarlyWarningPredictor(model_type="random_forest", observation_weeks=6)
        metrics = predictor.train_and_evaluate(self.cohort)

        self.assertNotIn("error", metrics)
        self.assertGreaterEqual(metrics["roc_auc"], 0.70)
        self.assertGreaterEqual(metrics["accuracy"], 0.70)
        self.assertIn("feature_importances", metrics)
        self.assertEqual(len(metrics["feature_importances"]), 8)

    def test_real_time_inference(self):
        predictor = EarlyWarningPredictor(model_type="random_forest", observation_weeks=6)
        predictor.train_and_evaluate(self.cohort)

        # High risk profile
        high_risk_features = {
            "early_attendance_rate": 0.75,
            "early_tardy_rate": 0.25,
            "early_unexcused_rate": 0.15,
            "early_avg_daily_lms_minutes": 15.0,
            "early_lms_trend_decay": 0.50,
            "early_submission_rate": 0.60,
            "early_quiz_average": 60.0,
            "baseline_gpa": 2.1,
        }
        res_high = predictor.predict_risk(high_risk_features)
        self.assertIn(res_high["predicted_risk_tier"], ["ELEVATED", "CRITICAL", "MODERATE"])

        # Low risk profile
        low_risk_features = {
            "early_attendance_rate": 0.98,
            "early_tardy_rate": 0.02,
            "early_unexcused_rate": 0.0,
            "early_avg_daily_lms_minutes": 70.0,
            "early_lms_trend_decay": -0.10,
            "early_submission_rate": 0.98,
            "early_quiz_average": 90.0,
            "baseline_gpa": 3.8,
        }
        res_low = predictor.predict_risk(low_risk_features)
        self.assertEqual(res_low["predicted_risk_tier"], "LOW")


if __name__ == "__main__":
    unittest.main()

