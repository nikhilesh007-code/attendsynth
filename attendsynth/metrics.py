"""Statistical fidelity metrics and benchmark comparison suite."""

from typing import Any, Dict, List, Tuple
import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon


class FidelityEvaluator:
    """Evaluates statistical fidelity and distributional coherence of synthetic cohort data."""

    def __init__(self):
        # Empirical educational benchmarks (based on published K-12 and blended LMS learning research)
        self.empirical_attendance_mean = 0.885
        self.empirical_attendance_std = 0.095
        self.empirical_lms_minutes_mean = 52.0
        self.empirical_lms_minutes_std = 22.0
        self.empirical_chronic_rate = 0.180

    def evaluate(self, students: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Computes comprehensive fidelity scores against educational research baselines."""
        if not students:
            return {"error": "Empty student cohort"}

        att_rates = np.array([s["attendance_rate"] for s in students])
        lms_mins = np.array([s["avg_daily_lms_minutes"] for s in students])
        sub_rates = np.array([s["assignment_submission_rate"] for s in students])
        quiz_scores = np.array([s["average_quiz_score"] for s in students])

        # 1. KS-Test for Attendance Distribution
        ref_att_sample = np.random.normal(
            self.empirical_attendance_mean, self.empirical_attendance_std, size=len(students)
        )
        ref_att_sample = np.clip(ref_att_sample, 0.40, 0.99)
        ks_att = stats.ks_2samp(att_rates, ref_att_sample)

        # 2. KS-Test for LMS Minutes Distribution
        ref_lms_sample = np.random.normal(
            self.empirical_lms_minutes_mean, self.empirical_lms_minutes_std, size=len(students)
        )
        ref_lms_sample = np.clip(ref_lms_sample, 5.0, 180.0)
        ks_lms = stats.ks_2samp(lms_mins, ref_lms_sample)

        # 3. Categorical Status Jensen-Shannon Divergence
        status_jsd = self._compute_attendance_jsd(students)

        # 4. Correlation Preservation Matrix
        corr_matrix, corr_fidelity = self._compute_correlation_fidelity(
            att_rates, lms_mins, sub_rates, quiz_scores
        )

        # 5. Composite Synthetic Quality Score (SQS, 0-100)
        # Low KS statistic is good, low JSD is good, high correlation match is good
        att_score = max(0.0, 1.0 - float(ks_att.statistic)) * 30.0
        lms_score = max(0.0, 1.0 - float(ks_lms.statistic)) * 25.0
        jsd_score = max(0.0, 1.0 - float(status_jsd)) * 20.0
        corr_score = corr_fidelity * 25.0

        sqs_total = round(float(np.clip(att_score + lms_score + jsd_score + corr_score, 0.0, 100.0)), 1)

        return {
            "synthetic_quality_score": sqs_total,
            "quality_grade": "Excellent (Production Grade)" if sqs_total >= 85 else (
                "Good (Viable for Model Training)" if sqs_total >= 70 else "Needs Tuning"
            ),
            "ks_tests": {
                "attendance_rate": {
                    "statistic": round(float(ks_att.statistic), 4),
                    "p_value": round(float(ks_att.pvalue), 4),
                    "passed": bool(ks_att.statistic < 0.25),
                },
                "lms_active_minutes": {
                    "statistic": round(float(ks_lms.statistic), 4),
                    "p_value": round(float(ks_lms.pvalue), 4),
                    "passed": bool(ks_lms.statistic < 0.25),
                },
            },
            "jensen_shannon_divergence": {
                "attendance_distribution_jsd": round(float(status_jsd), 4),
                "passed": bool(status_jsd < 0.20),
            },
            "correlations": {
                "features": ["Attendance Rate", "LMS Minutes", "Submission Rate", "Quiz Score"],
                "matrix": corr_matrix,
                "correlation_fidelity_score": round(float(corr_fidelity), 3),
            },
            "comparison_summary": {
                "synthetic_mean_attendance": round(float(np.mean(att_rates)), 3),
                "empirical_mean_attendance": self.empirical_attendance_mean,
                "synthetic_mean_lms_minutes": round(float(np.mean(lms_mins)), 1),
                "empirical_mean_lms_minutes": self.empirical_lms_minutes_mean,
            },
        }

    def _compute_attendance_jsd(self, students: List[Dict[str, Any]]) -> float:
        """Computes JSD between synthetic attendance status distribution and historical ed-tech norms."""
        # Baseline real-world proportions: [Present: 88%, Tardy: 4%, Excused: 5%, Unexcused: 3%]
        p_ref = np.array([0.88, 0.04, 0.05, 0.03])

        total_p = sum(s["days_present"] for s in students)
        total_t = sum(s["days_tardy"] for s in students)
        total_e = sum(s["excused_absences"] for s in students)
        total_u = sum(s["unexcused_absences"] for s in students)
        grand_total = max(1, total_p + total_t + total_e + total_u)

        q_synth = np.array([total_p, total_t, total_e, total_u]) / grand_total
        # Jensen-Shannon distance is square root of JSD, jensenshannon in scipy returns distance
        js_dist = jensenshannon(p_ref, q_synth)
        return float(js_dist)

    def _compute_correlation_fidelity(
        self,
        att_rates: np.ndarray,
        lms_mins: np.ndarray,
        sub_rates: np.ndarray,
        quiz_scores: np.ndarray,
    ) -> Tuple[List[List[float]], float]:
        """Calculates internal Pearson correlation matrix and evaluates realistic cross-feature alignment."""
        data_matrix = np.column_stack([att_rates, lms_mins, sub_rates, quiz_scores])
        corr = np.corrcoef(data_matrix, rowvar=False)
        corr_list = [[round(float(val), 3) for val in row] for row in corr]

        # In real education data, attendance, LMS time, assignment submission, and quiz scores
        # are positively correlated (typically r ~ 0.40 to 0.75)
        expected_positives = [
            corr[0, 1],  # att <-> lms
            corr[0, 2],  # att <-> sub
            corr[0, 3],  # att <-> quiz
            corr[1, 2],  # lms <-> sub
            corr[1, 3],  # lms <-> quiz
            corr[2, 3],  # sub <-> quiz
        ]
        positive_alignments = sum(1 for r in expected_positives if 0.20 <= r <= 0.85)
        corr_fidelity = round(positive_alignments / len(expected_positives), 3)

        return corr_list, corr_fidelity
