"""
Engagement and Academic Risk Engine for AttendSynth AI.
Implements transparent institutional formulas:
- Engagement Score = 0.35 * Attendance + 0.25 * Participation + 0.20 * LMS + 0.20 * Assignment Completion
- Risk Score = 0.35 * (100 - Attendance) + 0.25 * (100 - Participation) + 0.20 * (100 - Assignment) + 0.20 * (100 - LMS)
- Risk Classification:
    0 - 29: Low
    30 - 59: Medium
    60 - 100: High
Configurable institutional weights; longitudinal weekly trend analysis (Improving / Stable / Declining).
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class EarlyWarningEngine:
    """Evaluates student records using transparent multi-factor institutional criteria."""

    # Default configurable weights (Institutional assumptions; documented, not empirical universals)
    DEFAULT_WEIGHTS = {
        "attendance": 0.35,
        "participation": 0.25,
        "assignment": 0.20,
        "lms": 0.20,
    }

    # Explicit threshold triggers for academic warnings
    THRESHOLDS = {
        "attendance_critical": 60.0,
        "assignments_lagging": 50.0,
        "marks_failing": 50.0,
        "participation_deficient": 40.0,
        "lms_inactive": 40.0,
        "late_chronic": 4,
    }

    @classmethod
    def calculate_engagement_score(
        cls,
        attendance_pct: float,
        participation_score: float,
        lms_score: float,
        assignment_completion_pct: float,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculates Engagement Score = 0.35*Att + 0.25*Part + 0.20*LMS + 0.20*Assign.
        All inputs normalized to 0-100 scale.
        """
        w = weights or cls.DEFAULT_WEIGHTS
        att = min(100.0, max(0.0, float(attendance_pct)))
        part = min(100.0, max(0.0, float(participation_score)))
        lms = min(100.0, max(0.0, float(lms_score)))
        assign = min(100.0, max(0.0, float(assignment_completion_pct)))

        raw = (
            w.get("attendance", 0.35) * att
            + w.get("participation", 0.25) * part
            + w.get("lms", 0.20) * lms
            + w.get("assignment", 0.20) * assign
        )
        return round(float(min(100.0, max(0.0, raw))), 1)

    @classmethod
    def calculate_student_risk(
        cls,
        attendance_pct: float,
        assignment_completion_pct: float,
        avg_marks: float = 75.0,
        participation_score: float = 75.0,
        late_submissions: int = 0,
        weekly_trajectory: str = "Stable",
        lms_logins_per_week: float = 20.0,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates a calibrated, multi-factor academic risk score strictly between 0 and 100.
        Risk Score = 0.35*(100 - Att) + 0.25*(100 - Part) + 0.20*(100 - Assign) + 0.20*(100 - LMS).
        Avoids artificial clamping to 100 by using a bounded linear deficit model.
        """
        w = weights or cls.DEFAULT_WEIGHTS

        att = min(100.0, max(0.0, float(attendance_pct)))
        assign = min(100.0, max(0.0, float(assignment_completion_pct)))
        part = min(100.0, max(0.0, float(participation_score)))

        # Normalize LMS activity to 0-100 scale (20 logins/wk = 100%)
        lms_norm = min(100.0, max(0.0, (float(lms_logins_per_week) / 20.0) * 100.0))

        # Deficits
        att_def = round(w.get("attendance", 0.35) * (100.0 - att), 1)
        part_def = round(w.get("participation", 0.25) * (100.0 - part), 1)
        assign_def = round(w.get("assignment", 0.20) * (100.0 - assign), 1)
        lms_def = round(w.get("lms", 0.20) * (100.0 - lms_norm), 1)

        # Marks penalty contribution if failing (<50)
        marks_penalty = round(max(0.0, (50.0 - float(avg_marks)) * 0.1), 1) if avg_marks < 50.0 else 0.0
        decay_penalty = 3.0 if weekly_trajectory == "Declining" else 0.0

        breakdown = {
            "attendance_deficit": att_def,
            "assignment_deficit": assign_def,
            "marks_deficit": marks_penalty,
            "participation_deficit": part_def,
            "behavior_penalty": round(lms_def + decay_penalty, 1),
        }

        # Composite score strictly bounded [0, 100] summing breakdown values
        risk_score = round(float(min(100.0, max(0.0, sum(breakdown.values())))), 1)

        # Flags
        flags = []
        if att < cls.THRESHOLDS["attendance_critical"]:
            flags.append(f"Attendance critically low ({att:.1f}% < 60%)")
        if assign < cls.THRESHOLDS["assignments_lagging"]:
            flags.append(f"Assignment completion lagging ({assign:.1f}% < 50%)")
        if avg_marks < cls.THRESHOLDS["marks_failing"]:
            flags.append(f"Formative marks below passing ({avg_marks:.1f}% < 50%)")
        if part < cls.THRESHOLDS["participation_deficient"]:
            flags.append(f"In-class participation deficient ({part:.1f} < 40)")
        if lms_norm < cls.THRESHOLDS["lms_inactive"]:
            flags.append(f"LMS telemetry inactive ({lms_logins_per_week:.1f} logins/wk)")
        if late_submissions >= cls.THRESHOLDS["late_chronic"]:
            flags.append(f"Chronic late submissions ({late_submissions} overdue)")
        if weekly_trajectory == "Declining":
            flags.append("Multi-week engagement decay pattern detected")

        # Classify into standard institutional tiers
        # 0-29: Low, 30-59: Medium, 60-100: High
        if risk_score >= 60.0:
            risk_level = "High"
            rec = "Tier 3: Immediate 1-on-1 counselor outreach and individualized academic success plan."
        elif risk_score >= 30.0:
            risk_level = "Medium"
            rec = "Tier 2: Targeted peer-tutoring check-in and automated assignment deadline notifications."
        else:
            risk_level = "Low"
            rec = "Tier 1: Standard universal curriculum engagement and pacing guidelines."

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "indicator_breakdown": breakdown,
            "flagged_reasons": flags,
            "support_recommendation": rec,
        }

    @classmethod
    def analyze_weekly_trend(cls, weekly_scores: List[float]) -> str:
        """Determines longitudinal trajectory: Improving, Stable, or Declining."""
        if not weekly_scores or len(weekly_scores) < 4:
            return "Stable"

        mid = len(weekly_scores) // 2
        first_half_avg = float(np.mean(weekly_scores[:mid]))
        second_half_avg = float(np.mean(weekly_scores[mid:]))
        delta = second_half_avg - first_half_avg

        if delta > 3.0:
            return "Improving"
        elif delta < -3.0:
            return "Declining"
        return "Stable"

    @classmethod
    def evaluate_cohort(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyzes cohort data, aggregates risk tiers, reasons breakdown,
        and provides Multi-Tiered System of Supports (MTSS) recommendations.
        """
        if df.empty:
            return {
                "total_students": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "flagged_students": [],
                "reasons_breakdown": {},
                "mtss_recommendations": {},
            }

        high_risk_mask = df["risk_level"] == "High"
        medium_risk_mask = df["risk_level"] == "Medium"
        low_risk_mask = df["risk_level"] == "Low"

        # Flagged count breakdown
        reasons_count = {
            "Attendance critically low (<60%)": int((df["attendance_pct"] < cls.THRESHOLDS["attendance_critical"]).sum()),
            "Assignment completion lagging (<50%)": int((df["assignment_completion_pct"] < cls.THRESHOLDS["assignments_lagging"]).sum()),
            "In-class participation deficient (<40%)": int((df["participation_score"] < cls.THRESHOLDS["participation_deficient"]).sum()),
            "Formative marks below passing (<50%)": int((df["avg_marks"] < cls.THRESHOLDS["marks_failing"]).sum()),
            "Chronic late submissions (≥4 overdue)": int((df["late_submissions"] >= cls.THRESHOLDS["late_chronic"]).sum()),
            "Multi-week engagement decay": int((df["weekly_trajectory"] == "Declining").sum()),
        }

        # Students requiring priority attention (High and Medium risk)
        flagged_df = df[high_risk_mask | medium_risk_mask].sort_values(by="risk_score", ascending=False)
        flagged_list = []
        for _, row in flagged_df.head(100).iterrows():
            flagged_list.append({
                "id": str(row.get("student_id", row.get("id"))),
                "name": str(row["name"]),
                "course": str(row["course"]),
                "attendance_pct": float(row["attendance_pct"]),
                "participation_score": float(row["participation_score"]),
                "assignment_completion_pct": float(row["assignment_completion_pct"]),
                "late_submissions": int(row["late_submissions"]),
                "risk_score": float(row["risk_score"]),
                "risk_level": str(row["risk_level"]),
                "flagged_reasons": row["flagged_reasons"] if isinstance(row.get("flagged_reasons"), list) else [],
                "support_recommendation": str(row.get("support_recommendation", "")),
            })

        high_cnt = int(high_risk_mask.sum())
        med_cnt = int(medium_risk_mask.sum())
        low_cnt = int(low_risk_mask.sum())

        return {
            "total_students": len(df),
            "high_risk_count": high_cnt,
            "medium_risk_count": med_cnt,
            "low_risk_count": low_cnt,
            "flagged_students": flagged_list,
            "reasons_breakdown": reasons_count,
            "mtss_recommendations": {
                "Tier 1 (Universal Support)": [
                    "Deploy automated weekly LMS assignment deadline reminders via email/SMS.",
                    "Provide asynchronous lecture recordings and transcript notes for missed sessions.",
                    "Maintain active syllabus pacing guide and interactive weekly discussion prompts.",
                ],
                "Tier 2 (Targeted Support)": [
                    f"Initiate peer tutoring matches for the {med_cnt} moderate-risk students.",
                    "Schedule collaborative study hall check-ins for students with 1-2 missed deadlines.",
                    "Offer low-stakes formative knowledge checks to rebuild academic momentum.",
                ],
                "Tier 3 (Intensive Support)": [
                    f"Conduct mandatory 1-on-1 academic counseling for all {high_cnt} high-risk students.",
                    "Formulate individual student success plans with course instructors and advisors.",
                    "Audit potential personal, technological, or schedule impediments causing chronic absence.",
                ],
            },
        }
