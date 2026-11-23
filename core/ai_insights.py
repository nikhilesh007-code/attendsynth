"""
Groq API Integration Engine for AttendSynth AI.
Provides ultra-fast AI insights, pedagogical diagnostics, and MTSS intervention planning.
"""

import os
from typing import Dict, Any, Optional
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class GroqInsightsEngine:
    """Manages AI-driven analytical queries using the official Groq Python SDK."""

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    FAST_MODEL = "llama-3.1-8b-instant"

    @classmethod
    def get_api_key(cls, user_provided_key: Optional[str] = None) -> Optional[str]:
        """Resolves the Groq API key from user input, environment variables, or .env."""
        if user_provided_key and user_provided_key.strip():
            return user_provided_key.strip()
        env_key = os.environ.get("GROQ_API_KEY", "")
        return env_key.strip() if env_key.strip() else None

    @classmethod
    def build_aggregate_context(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Creates privacy-safe aggregate statistics to send to Groq.
        Zero individual student personal records are transmitted.
        """
        if df.empty:
            return {}

        total = len(df)
        avg_att = df["attendance_pct"].mean()
        avg_eng = df["engagement_score"].mean()
        avg_marks = df["avg_marks"].mean()
        avg_assign = df["assignment_completion_pct"].mean()
        avg_lms = df["lms_logins_per_week"].mean()

        risk_dist = df["risk_level"].value_counts().to_dict()
        eng_dist = df["engagement_level"].value_counts().to_dict()
        traj_dist = df["weekly_trajectory"].value_counts().to_dict()

        # Severe indicators
        att_under_60 = int((df["attendance_pct"] < 60.0).sum())
        assign_under_50 = int((df["assignment_completion_pct"] < 50.0).sum())
        part_under_40 = int((df["participation_score"] < 40.0).sum())

        course_summary = df.groupby("course")["engagement_score"].mean().round(1).to_dict()

        return {
            "total_students": total,
            "average_attendance_pct": round(float(avg_att), 1),
            "average_engagement_score": round(float(avg_eng), 1),
            "average_marks": round(float(avg_marks), 1),
            "average_assignment_completion_pct": round(float(avg_assign), 1),
            "average_lms_logins_weekly": round(float(avg_lms), 1),
            "risk_distribution": risk_dist,
            "engagement_distribution": eng_dist,
            "weekly_trajectories": traj_dist,
            "students_with_attendance_under_60pct": att_under_60,
            "students_with_assignments_under_50pct": assign_under_50,
            "students_with_participation_under_40pct": part_under_40,
            "course_average_engagement": course_summary,
        }

    @classmethod
    def generate_insight(
        cls,
        df: pd.DataFrame,
        user_query: str,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ) -> Dict[str, Any]:
        """Queries Groq LLM with aggregate context and returns structured insights."""
        resolved_key = cls.get_api_key(api_key)

        if not resolved_key:
            return {
                "success": False,
                "error": "MISSING_API_KEY",
                "message": (
                    "Groq API Key is not configured. Please paste your free Groq API key in the "
                    "input field or add GROQ_API_KEY to your .env file."
                ),
                "fallback": cls.generate_heuristic_fallback(df, user_query),
            }

        context = cls.build_aggregate_context(df)
        if not context:
            return {"success": False, "error": "EMPTY_DATASET", "message": "Dataset is empty."}

        system_prompt = (
            "You are AttendSynth AI's Chief Education Data Scientist and Early Warning System Specialist. "
            "You analyze synthetic student engagement datasets to help EdTech platforms, school leaders, and "
            "academic counselors detect disengagement patterns early.\n\n"
            "Analyze the provided aggregate cohort statistics strictly based on the provided numbers. "
            "Never invent fabricated statistics. Structure your output clearly into:\n"
            "1. 📊 Dataset Observations\n"
            "2. 🔍 Engagement Patterns & Trends\n"
            "3. ⚠️ Possible Contributing Factors\n"
            "4. 🚨 Risk Analysis & Vulnerability Assessment\n"
            "5. 🎯 Multi-Tiered Actionable Recommendations (MTSS Tier 1, 2, 3)\n"
            "6. 📌 Concise Executive Conclusion"
        )

        user_prompt = f"""
Dataset Aggregate Summary:
- Cohort Size: {context['total_students']} Students
- Mean Attendance: {context['average_attendance_pct']}%
- Mean Engagement Index: {context['average_engagement_score']} / 100
- Mean Assessment Marks: {context['average_marks']}%
- Mean Assignment Completion: {context['average_assignment_completion_pct']}%
- Mean Weekly LMS Logins: {context['average_lms_logins_weekly']}
- Risk Distribution: {context['risk_distribution']}
- Engagement Tiers: {context['engagement_distribution']}
- Longitudinal Trajectories: {context['weekly_trajectories']}
- Attendance Under 60%: {context['students_with_attendance_under_60pct']} students
- Assignments Under 50%: {context['students_with_assignments_under_50pct']} students
- In-Class Participation Under 40%: {context['students_with_participation_under_40pct']} students
- Course Breakdown: {context['course_average_engagement']}

User Question / Objective:
"{user_query}"

Provide your professional, structured pedagogical and data science analysis:
"""

        try:
            from groq import Groq

            client = Groq(api_key=resolved_key)
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            response_text = completion.choices[0].message.content
            return {
                "success": True,
                "response": response_text,
                "model_used": model,
                "tokens_used": completion.usage.total_tokens if completion.usage else None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": "API_CALL_FAILED",
                "message": f"Groq API call error: {str(e)}",
                "fallback": cls.generate_heuristic_fallback(df, user_query),
            }

    @classmethod
    def generate_heuristic_fallback(cls, df: pd.DataFrame, query: str) -> str:
        """Rule-based statistical narrative if Groq API is offline or key is unconfigured."""
        context = cls.build_aggregate_context(df)
        if not context:
            return "No data available."

        high_risk = context['risk_distribution'].get('High', 0)
        tot = context['total_students']
        high_risk_pct = round((high_risk / tot) * 100, 1) if tot > 0 else 0

        return f"""### 📊 Automated Statistical Dataset Overview (Heuristic Offline Mode)

> *Note: This analysis was generated locally using rule-based descriptive statistics because the Groq API key is not currently connected.*

#### 1. Dataset Observations
- The generated cohort contains **{tot} synthetic students**.
- The cohort-wide average attendance rate is **{context['average_attendance_pct']}%**.
- The average composite engagement index is **{context['average_engagement_score']} / 100**.
- Average assignment completion rate stands at **{context['average_assignment_completion_pct']}%**.

#### 2. Risk & Vulnerability Analysis
- **{high_risk} students ({high_risk_pct}%)** meet the High-Risk threshold requiring immediate proactive outreach.
- **{context['students_with_attendance_under_60pct']} students** exhibit severe attendance deficits (<60%).
- **{context['students_with_assignments_under_50pct']} students** have completed less than 50% of coursework.

#### 3. Recommended Actions
1. **Tier 1 (Universal)**: Implement automated weekly LMS check-ins and assignment deadline SMS nudges.
2. **Tier 2 (Targeted)**: Connect the **{high_risk} high-risk students** with peer tutors for courses showing the lowest engagement.
3. **Tier 3 (Intensive)**: Schedule mandatory counselor 1-on-1 conferences for the **{context['students_with_attendance_under_60pct']} students** with chronic absence.
"""
