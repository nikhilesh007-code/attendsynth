"""
Dataset Analytics and Statistical Aggregation Engine for AttendSynth AI.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


class DatasetAnalytics:
    """Computes summary KPIs, course breakdowns, and correlation metrics."""

    @staticmethod
    def compute_summary_kpis(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates top-level executive metrics for dashboard display."""
        if df.empty:
            return {
                "total_students": 0,
                "avg_attendance": 0.0,
                "avg_engagement": 0.0,
                "avg_marks": 0.0,
                "avg_assignment_completion": 0.0,
                "high_engagement_count": 0,
                "medium_engagement_count": 0,
                "low_engagement_count": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "high_risk_pct": 0.0,
                "flagged_count": 0,
            }

        total = len(df)
        avg_att = float(df["attendance_pct"].mean())
        avg_eng = float(df["engagement_score"].mean())
        avg_marks = float(df["avg_marks"].mean())
        avg_assign = float(df["assignment_completion_pct"].mean())

        eng_counts = df["engagement_level"].value_counts().to_dict()
        risk_counts = df["risk_level"].value_counts().to_dict()

        high_risk = risk_counts.get("High", 0)

        # Flagged count (risk level High or Medium)
        flagged = high_risk + risk_counts.get("Medium", 0)

        return {
            "total_students": total,
            "avg_attendance": round(avg_att, 1),
            "avg_engagement": round(avg_eng, 1),
            "avg_marks": round(avg_marks, 1),
            "avg_assignment_completion": round(avg_assign, 1),
            "high_engagement_count": eng_counts.get("High", 0),
            "medium_engagement_count": eng_counts.get("Medium", 0),
            "low_engagement_count": eng_counts.get("Low", 0),
            "high_risk_count": high_risk,
            "medium_risk_count": risk_counts.get("Medium", 0),
            "low_risk_count": risk_counts.get("Low", 0),
            "high_risk_pct": round((high_risk / total) * 100.0, 1) if total > 0 else 0.0,
            "flagged_count": flagged,
        }

    @staticmethod
    def get_course_breakdown(df: pd.DataFrame) -> pd.DataFrame:
        """Returns course-by-course average telemetry."""
        if df.empty:
            return pd.DataFrame()

        grouped = df.groupby("course").agg(
            Student_Count=("student_id", "count"),
            Avg_Attendance=("attendance_pct", "mean"),
            Avg_Engagement=("engagement_score", "mean"),
            Avg_Marks=("avg_marks", "mean"),
            Avg_Assignments=("assignment_completion_pct", "mean"),
            High_Risk_Count=("risk_level", lambda s: (s == "High").sum()),
        ).reset_index()

        for col in ["Avg_Attendance", "Avg_Engagement", "Avg_Marks", "Avg_Assignments"]:
            grouped[col] = grouped[col].round(1)

        return grouped

    @staticmethod
    def get_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
        """Computes Pearson correlation for numerical engagement indicators."""
        cols = [
            "attendance_pct",
            "participation_score",
            "assignment_completion_pct",
            "lms_logins_per_week",
            "avg_marks",
            "late_submissions",
            "engagement_score",
            "risk_score",
        ]
        valid_cols = [c for c in cols if c in df.columns]
        if len(valid_cols) < 2:
            return pd.DataFrame()
        return df[valid_cols].corr().round(2)
