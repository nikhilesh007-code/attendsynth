"""
Interactive What-If Scenario Simulator for AttendSynth AI.
Evaluates the impact of hypothetical policy interventions on student risk and engagement.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


class ScenarioSimulator:
    """Simulates hypothetical changes in attendance, participation, and LMS usage."""

    @classmethod
    def run_simulation(
        cls,
        base_df: pd.DataFrame,
        att_delta: float = 0.0,
        part_delta: float = 0.0,
        assign_delta: float = 0.0,
        lms_delta: float = 0.0,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Applies deltas to baseline student data and recalculates synthetic engagement & risk.
        All deltas are percentages (e.g. +10.0 means +10%).
        """
        if base_df.empty:
            return base_df, {}

        sim_df = base_df.copy()

        # Apply shifts with realistic clamping [0, 100]
        sim_df["attendance_pct"] = np.clip(sim_df["attendance_pct"] + att_delta, 0.0, 100.0).round(1)
        sim_df["participation_score"] = np.clip(sim_df["participation_score"] + part_delta, 0.0, 100.0).round(1)
        sim_df["assignment_completion_pct"] = np.clip(sim_df["assignment_completion_pct"] + assign_delta, 0.0, 100.0).round(1)
        sim_df["lms_logins_per_week"] = np.clip(sim_df["lms_logins_per_week"] * (1.0 + lms_delta / 100.0), 0.5, 35.0).round(1)

        # Recalculate engagement score
        lms_norm = np.clip((sim_df["lms_logins_per_week"] / 18.0) * 100.0, 0.0, 100.0)
        new_eng = (
            (0.35 * sim_df["attendance_pct"])
            + (0.25 * sim_df["participation_score"])
            + (0.25 * sim_df["assignment_completion_pct"])
            + (0.15 * lms_norm)
            - (sim_df["late_submissions"] * 1.5)
        )
        sim_df["engagement_score"] = np.clip(new_eng, 5.0, 100.0).round(1)

        sim_df["engagement_level"] = sim_df["engagement_score"].apply(
            lambda s: "High" if s >= 75.0 else ("Medium" if s >= 50.0 else "Low")
        )

        # Recalculate risk score
        base_risk = 100.0 - sim_df["engagement_score"]
        penalties = np.zeros(len(sim_df))
        penalties += np.where(sim_df["attendance_pct"] < 60.0, 15.0, 0.0)
        penalties += np.where(sim_df["assignment_completion_pct"] < 50.0, 12.0, 0.0)
        penalties += np.where(sim_df["participation_score"] < 40.0, 10.0, 0.0)
        penalties += np.where(sim_df["avg_marks"] < 50.0, 12.0, 0.0)
        penalties += np.where(sim_df["late_submissions"] >= 4, 8.0, 0.0)

        sim_df["risk_score"] = np.clip(base_risk * 0.7 + penalties, 0.0, 100.0).round(1)
        sim_df["risk_level"] = sim_df["risk_score"].apply(
            lambda r: "High" if r >= 65.0 else ("Medium" if r >= 35.0 else "Low")
        )

        # Comparison summary metrics
        base_high_risk = int((base_df["risk_level"] == "High").sum())
        sim_high_risk = int((sim_df["risk_level"] == "High").sum())
        saved_from_high_risk = base_high_risk - sim_high_risk

        summary = {
            "baseline_avg_attendance": round(float(base_df["attendance_pct"].mean()), 1),
            "sim_avg_attendance": round(float(sim_df["attendance_pct"].mean()), 1),
            "baseline_avg_engagement": round(float(base_df["engagement_score"].mean()), 1),
            "sim_avg_engagement": round(float(sim_df["engagement_score"].mean()), 1),
            "baseline_high_risk_count": base_high_risk,
            "sim_high_risk_count": sim_high_risk,
            "students_saved_from_high_risk": saved_from_high_risk,
            "relative_risk_reduction_pct": round(
                ((base_high_risk - sim_high_risk) / max(1, base_high_risk)) * 100.0, 1
            ),
        }

        return sim_df, summary
