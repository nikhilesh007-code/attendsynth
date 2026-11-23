"""
Transparent Rule-Based Early Warning System (EWS) Engine for AttendSynth AI.
Evaluates student engagement telemetry, flags vulnerable learners, and suggests interventions.
"""

from typing import Dict, List, Tuple
import pandas as pd


class EarlyWarningEngine:
    """Rule-based Academic Risk and Early Intervention Evaluation Engine."""

    # Transparent rule thresholds
    ATTENDANCE_CRITICAL = 60.0
    PARTICIPATION_CRITICAL = 40.0
    ASSIGNMENT_CRITICAL = 50.0
    MARKS_CRITICAL = 50.0
    LATE_SUBMISSIONS_CRITICAL = 4

    @classmethod
    def evaluate_student(cls, student: pd.Series) -> Dict:
        """Evaluates transparent academic risk indicators for a single student."""
        reasons = []
        actions = []
        score = 0.0

        # Rule 1: Critical Attendance
        att = student.get("attendance_pct", 100.0)
        if att < cls.ATTENDANCE_CRITICAL:
            reasons.append(f"Severe Attendance Crisis ({att:.1f}% < {cls.ATTENDANCE_CRITICAL}%)")
            actions.append("Automated Attendance SMS Nudge & Counselor Family Outreach")
            score += 30.0
        elif att < 75.0:
            reasons.append(f"Moderate Attendance Deficit ({att:.1f}% < 75%)")
            actions.append("Advisor Attendance Check-in")
            score += 15.0

        # Rule 2: Assignment Neglect
        assign = student.get("assignment_completion_pct", 100.0)
        if assign < cls.ASSIGNMENT_CRITICAL:
            reasons.append(f"Low Assignment Completion ({assign:.1f}% < {cls.ASSIGNMENT_CRITICAL}%)")
            actions.append("Structured Assignment Recovery Plan & Homework Clinic")
            score += 25.0
        elif assign < 70.0:
            reasons.append(f"Borderline Assignment Submission ({assign:.1f}% < 70%)")
            score += 10.0

        # Rule 3: Classroom Disengagement
        part = student.get("participation_score", 100.0)
        if part < cls.PARTICIPATION_CRITICAL:
            reasons.append(f"Low In-Class Participation ({part:.1f} < {cls.PARTICIPATION_CRITICAL})")
            actions.append("Instructor 1-on-1 Office Hours & Collaborative Study Group")
            score += 20.0

        # Rule 4: Academic Underperformance
        marks = student.get("avg_marks", 100.0)
        if marks < cls.MARKS_CRITICAL:
            reasons.append(f"Failing Assessment Average ({marks:.1f}% < {cls.MARKS_CRITICAL}%)")
            actions.append("Subject-Specific Peer Tutoring & Exam Preparation Clinic")
            score += 20.0

        # Rule 5: Habitual Late Submissions
        late = student.get("late_submissions", 0)
        if late >= cls.LATE_SUBMISSIONS_CRITICAL:
            reasons.append(f"Chronic Late Work ({late} late submissions >= {cls.LATE_SUBMISSIONS_CRITICAL})")
            actions.append("Time-Management & Academic Coaching Workshop")
            score += 15.0

        # Rule 6: Longitudinal Engagement Decay
        traj = student.get("weekly_trajectory", "Stable")
        if traj == "Declining":
            reasons.append("Multi-Week Longitudinal Engagement Decay")
            actions.append("Tier-2 MTSS Early-Warning Multi-Disciplinary Team Review")
            score += 15.0

        # Base risk adjustment from engagement score
        eng = student.get("engagement_score", 100.0)
        base_risk = max(0.0, (100.0 - eng) * 0.4)
        total_risk_score = min(100.0, base_risk + score)

        if total_risk_score >= 65.0:
            level = "High"
        elif total_risk_score >= 35.0:
            level = "Medium"
        else:
            level = "Low"

        # Unique actions
        dedup_actions = list(dict.fromkeys(actions))
        if not dedup_actions:
            dedup_actions = ["On Track: Standard Positive Reinforcement & Routine Monitoring"]

        return {
            "risk_score": round(total_risk_score, 1),
            "risk_level": level,
            "is_flagged": len(reasons) > 0 or level in ["High", "Medium"],
            "flag_reasons": reasons,
            "suggested_actions": dedup_actions,
            "trigger_count": len(reasons),
        }

    @classmethod
    def evaluate_cohort(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Applies EWS transparent rules across the entire student dataframe."""
        if df.empty:
            return df

        results = df.apply(cls.evaluate_student, axis=1)
        eval_df = df.copy()
        eval_df["ews_risk_score"] = [r["risk_score"] for r in results]
        eval_df["ews_risk_level"] = [r["risk_level"] for r in results]
        eval_df["is_flagged"] = [r["is_flagged"] for r in results]
        eval_df["flag_reasons"] = [r["flag_reasons"] for r in results]
        eval_df["suggested_actions"] = [r["suggested_actions"] for r in results]
        eval_df["trigger_count"] = [r["trigger_count"] for r in results]
        return eval_df
