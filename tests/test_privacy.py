"""Unit tests for privacy auditing and Differential Privacy engine."""

import unittest
from attendsynth.config import Presets
from attendsynth.generator import AttendSynthGenerator
from attendsynth.privacy import DifferentialPrivacyEngine, PrivacyAuditor


class TestPrivacy(unittest.TestCase):

    def setUp(self):
        cfg = Presets.standard_district(num_students=60, seed=42)
        generator = AttendSynthGenerator(cfg)
        self.cohort = generator.generate()

    def test_zero_pii_compliance(self):
        auditor = PrivacyAuditor(k_threshold=5)
        report = auditor.audit_cohort(self.cohort["students"])
        self.assertTrue(report["zero_pii_check"]["is_compliant"])
        self.assertTrue(report["zero_pii_check"]["no_email_leaks"])
        self.assertTrue(report["zero_pii_check"]["no_national_identifier_leaks"])

    def test_k_anonymity(self):
        auditor = PrivacyAuditor(k_threshold=3)
        report = auditor.audit_cohort(self.cohort["students"])
        self.assertIn("k_anonymity_score", report["k_anonymity"])
        self.assertGreaterEqual(report["k_anonymity"]["protected_student_ratio"], 0.5)

    def test_differential_privacy_engine(self):
        engine = DifferentialPrivacyEngine(epsilon=1.0, random_seed=42)
        original_count = 100
        noisy_count = engine.privatize_count(original_count, sensitivity=1.0)
        self.assertGreaterEqual(noisy_count, 0)
        # Check bounded mean
        noisy_mean = engine.privatize_mean(0.92, n_records=100, lower_bound=0.0, upper_bound=1.0)
        self.assertGreaterEqual(noisy_mean, 0.0)
        self.assertLessEqual(noisy_mean, 1.0)


if __name__ == "__main__":
    unittest.main()

