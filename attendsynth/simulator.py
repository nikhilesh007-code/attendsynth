"""What-If Policy and Intervention Simulation engine."""

from typing import Any, Dict, List
import copy
import numpy as np

from attendsynth.config import ArchetypeType, CohortConfig
from attendsynth.generator import AttendSynthGenerator


class PolicySimulator:
    """Simulates school district intervention policies on student engagement trajectories."""

    @staticmethod
    def simulate_policy_intervention(
        base_cohort: Dict[str, Any],
        policy_name: str,
        intervention_intensity: float = 0.5,
    ) -> Dict[str, Any]:
        """Evaluates how proactive interventions alter cohort outcomes.
        
        Policies:
        1. 'automated_sms_nudge': Early alerts sent to parents for tardies/absences (recovers 35% of gradual disengagers).
        2. 'counselor_case_management': Dedicated counselor check-in at week 5 (recovers 60% of elevated-risk students).
        3. 'friday_transport_support': Alleviates Monday/Friday drop-offs for sporadic attendees.
        """
        students = copy.deepcopy(base_cohort.get("students", []))
        n = len(students)
        if n == 0:
            return {"error": "Empty cohort"}

        base_chronic_count = sum(1 for s in students if s["chronic_absenteeism_flag"])
        base_chronic_rate = base_chronic_count / n
        base_avg_attendance = float(np.mean([s["attendance_rate"] for s in students]))

        # Apply policy effects
        recovered_count = 0
        new_attendance_rates = []
        new_chronic_count = 0

        rng = np.random.RandomState(42)

        for s in students:
            att_rate = s["attendance_rate"]
            arch = s["archetype"]
            is_chronic = s["chronic_absenteeism_flag"]

            improved_att = att_rate

            if policy_name == "automated_sms_nudge":
                # Helps gradual disengagers and sporadic attendees early on
                if arch in [ArchetypeType.GRADUAL_DISENGAGER, ArchetypeType.SPORADIC_ATTENDEE]:
                    if rng.rand() < (0.45 * intervention_intensity):
                        boost = rng.uniform(0.04, 0.09)
                        improved_att = min(0.98, att_rate + boost)
                        recovered_count += 1

            elif policy_name == "counselor_case_management":
                # High-touch support for students who hit elevated/critical risk
                if s["risk_level"] in ["ELEVATED", "CRITICAL"]:
                    if rng.rand() < (0.65 * intervention_intensity):
                        boost = rng.uniform(0.06, 0.13)
                        improved_att = min(0.97, att_rate + boost)
                        recovered_count += 1

            elif policy_name == "friday_transport_support":
                # Specific alleviation for sporadic students
                if arch == ArchetypeType.SPORADIC_ATTENDEE:
                    if rng.rand() < (0.70 * intervention_intensity):
                        boost = rng.uniform(0.05, 0.11)
                        improved_att = min(0.96, att_rate + boost)
                        recovered_count += 1

            new_attendance_rates.append(improved_att)
            if (1.0 - improved_att) >= 0.10:
                new_chronic_count += 1

        new_chronic_rate = new_chronic_count / n
        new_avg_att = float(np.mean(new_attendance_rates))

        chronic_reduction_pct = round(
            ((base_chronic_rate - new_chronic_rate) / max(0.001, base_chronic_rate)) * 100.0,
            1,
        )

        return {
            "policy_name": policy_name,
            "intervention_intensity": intervention_intensity,
            "total_students": n,
            "students_positively_impacted": recovered_count,
            "baseline": {
                "chronic_absenteeism_rate": round(base_chronic_rate, 3),
                "chronic_students_count": base_chronic_count,
                "average_attendance_rate": round(base_avg_attendance, 3),
            },
            "post_intervention": {
                "chronic_absenteeism_rate": round(new_chronic_rate, 3),
                "chronic_students_count": new_chronic_count,
                "average_attendance_rate": round(new_avg_att, 3),
            },
            "relative_chronic_reduction_pct": chronic_reduction_pct,
            "students_saved_from_chronic_absenteeism": base_chronic_count - new_chronic_count,
        }

