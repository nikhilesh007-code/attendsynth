"""
Dataset Analytics Engine for AttendSynth AI.
Computes cohort KPIs, distributions, correlation matrices, and time series trends.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class AnalyticsEngine:
    """Computes comprehensive analytics across student and longitudinal records."""

    @classmethod
    def compute_summary_kpis(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates executive headline indicators."""
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
                "chronic_absent_count": 0,
            }

        total = len(df)
        return {
            "total_students": total,
            "avg_attendance": round(float(df["attendance_pct"].mean()), 1),
            "avg_engagement": round(float(df["engagement_score"].mean()), 1),
            "avg_marks": round(float(df["avg_marks"].mean()), 1),
            "avg_assignment_completion": round(float(df["assignment_completion_pct"].mean()), 1),
            "high_engagement_count": int((df["engagement_level"] == "High").sum()),
            "medium_engagement_count": int((df["engagement_level"] == "Medium").sum()),
            "low_engagement_count": int((df["engagement_level"] == "Low").sum()),
            "high_risk_count": int((df["risk_level"] == "High").sum()),
            "chronic_absent_count": int((df["attendance_pct"] < 60.0).sum()),
        }

    @classmethod
    def compute_distributions(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Computes chart-ready distributions for engagement, risk, attendance, and courses."""
        if df.empty:
            return {}

        # Engagement distribution (High, Medium, Low)
        eng_counts = df["engagement_level"].value_counts().to_dict()
        engagement_dist = [
            {"name": "High", "value": int(eng_counts.get("High", 0)), "color": "#10b981"},
            {"name": "Medium", "value": int(eng_counts.get("Medium", 0)), "color": "#f59e0b"},
            {"name": "Low", "value": int(eng_counts.get("Low", 0)), "color": "#ef4444"},
        ]

        # Risk distribution (Low, Medium, High)
        risk_counts = df["risk_level"].value_counts().to_dict()
        risk_dist = [
            {"name": "Low Risk", "value": int(risk_counts.get("Low", 0)), "color": "#10b981"},
            {"name": "Medium Risk", "value": int(risk_counts.get("Medium", 0)), "color": "#f59e0b"},
            {"name": "High Risk", "value": int(risk_counts.get("High", 0)), "color": "#ef4444"},
        ]

        # Attendance bins (<60%, 60-70%, 70-80%, 80-90%, 90-100%)
        bins = [0, 60, 70, 80, 90, 100]
        labels = ["< 60%", "60 - 70%", "70 - 80%", "80 - 90%", "90 - 100%"]
        df["att_bucket"] = pd.cut(df["attendance_pct"], bins=bins, labels=labels, include_lowest=True)
        att_binned = df["att_bucket"].value_counts().reindex(labels, fill_value=0)
        attendance_dist = [{"bin": str(label), "count": int(count)} for label, count in att_binned.items()]

        # Course breakdown
        course_grp = df.groupby("course").agg({
            "student_id": "count",
            "attendance_pct": "mean",
            "engagement_score": "mean",
            "assignment_completion_pct": "mean",
            "risk_score": "mean",
        }).reset_index()

        course_breakdown = []
        for _, r in course_grp.iterrows():
            course_breakdown.append({
                "course": r["course"],
                "students": int(r["student_id"]),
                "attendance": round(float(r["attendance_pct"]), 1),
                "engagement": round(float(r["engagement_score"]), 1),
                "assignment_completion": round(float(r["assignment_completion_pct"]), 1),
                "avg_risk": round(float(r["risk_score"]), 1),
            })

        return {
            "engagement_distribution": engagement_dist,
            "risk_distribution": risk_dist,
            "attendance_distribution": attendance_dist,
            "course_breakdown": course_breakdown,
        }

    @classmethod
    def compute_weekly_trends(cls, weekly_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Averages weekly trajectory for cohort-level trendline."""
        if weekly_df.empty:
            return []

        weekly_grp = weekly_df.groupby("week_number").agg({
            "engagement_score": "mean",
            "attendance_pct": "mean",
            "lms_active_minutes": "mean",
        }).reset_index()

        trend = []
        for _, r in weekly_grp.iterrows():
            trend.append({
                "week": f"Wk {int(r['week_number'])}",
                "week_number": int(r["week_number"]),
                "avg_engagement": round(float(r["engagement_score"]), 1),
                "avg_attendance": round(float(r["attendance_pct"]), 1),
                "avg_lms_minutes": round(float(r["lms_active_minutes"]), 1),
            })
        return trend
