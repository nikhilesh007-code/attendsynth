"""
Groq AI Insights Service for AttendSynth AI.
Optimized for Groq Free-Tier quotas (HTTP 429 rate limit prevention, 500 max tokens),
with honest connection state detection and transparent local statistical fallback.
"""

import os
import time
from typing import Dict, Any, Optional
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class GroqService:
    """Manages AI-driven pedagogical analysis and dataset summaries."""

    DEFAULT_FREE_TIER_MODEL = "openai/gpt-oss-20b"
    MAX_TOKENS = 400
    TEMPERATURE = 0.2

    @classmethod
    def get_api_key(cls, user_key: Optional[str] = None) -> Optional[str]:
        """Resolves API key from parameter or environment."""
        if user_key and user_key.strip():
            return user_key.strip()
        env_key = os.getenv("GROQ_API_KEY", "")
        return env_key.strip() if env_key.strip() else None

    @classmethod
    def get_default_model(cls) -> str:
        """Returns the configured model or free-tier default."""
        return os.getenv("GROQ_MODEL", cls.DEFAULT_FREE_TIER_MODEL)

    @classmethod
    def build_aggregate_context(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Creates zero-PII aggregate statistics for Groq."""
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
    def test_connection(cls, api_key: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes an honest connection ping to Groq.
        Differentiates API key presence from model completion success and rate limits.
        """
        resolved_key = cls.get_api_key(api_key)
        if not resolved_key:
            return {
                "success": False,
                "status": "API Key Missing",
                "message": "GROQ_API_KEY is not configured in .env.",
                "model": None,
                "latency_ms": None,
            }

        target_model = model or cls.get_default_model()
        start = time.time()

        try:
            from groq import Groq, RateLimitError, NotFoundError, AuthenticationError

            client = Groq(api_key=resolved_key)
            completion = client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": "Ping: answer with 1 word 'READY'."}],
                max_tokens=10,
                temperature=0.0,
            )
            latency = round((time.time() - start) * 1000, 1)
            reply = completion.choices[0].message.content.strip()

            return {
                "success": True,
                "status": "Groq Request Successful",
                "message": f"Connected to Groq ({target_model}). Ping latency: {latency}ms. Response: {reply}",
                "model": target_model,
                "latency_ms": latency,
            }
        except AuthenticationError:
            return {
                "success": False,
                "status": "Groq Temporarily Unavailable",
                "message": "Invalid Groq API key. Please check your credentials.",
                "model": target_model,
                "latency_ms": None,
            }
        except RateLimitError as e:
            retry_sec = None
            try:
                if hasattr(e, "response") and e.response is not None:
                    retry_sec = e.response.headers.get("retry-after")
            except Exception:
                pass
            msg = "Groq Free-Tier Rate Limit Reached (HTTP 429)."
            if retry_sec:
                msg += f" Retry available in {retry_sec}s."
            return {
                "success": False,
                "status": "Groq Rate Limited",
                "message": msg,
                "model": target_model,
                "retry_after": retry_sec,
            }
        except NotFoundError as e:
            return {
                "success": False,
                "status": "Groq Temporarily Unavailable",
                "message": f"Model '{target_model}' not found or inaccessible on this account.",
                "model": target_model,
                "latency_ms": None,
            }
        except Exception as e:
            return {
                "success": False,
                "status": "Groq Temporarily Unavailable",
                "message": f"Groq connection error: {str(e)}",
                "model": target_model,
                "latency_ms": None,
            }

    @classmethod
    def query(
        cls,
        df: pd.DataFrame,
        user_query: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Queries Groq with concise cohort aggregates or falls back to local statistical analysis."""
        resolved_key = cls.get_api_key(api_key)

        if not resolved_key:
            return {
                "success": False,
                "status": "Local Fallback Active",
                "is_fallback": True,
                "response": cls.generate_heuristic_fallback(df, user_query),
                "error": "GROQ_API_KEY is not configured. Displaying Local Statistical Analysis.",
                "model_used": None,
                "tokens_used": None,
            }

        context = cls.build_aggregate_context(df)
        if not context:
            return {
                "success": False,
                "status": "Local Fallback Active",
                "response": "Cohort dataset is empty.",
                "error": "Dataset is empty.",
                "is_fallback": True,
            }

        target_model = model or cls.get_default_model()

        system_prompt = (
            "You are AttendSynth AI Co-Pilot, an educational analytics assistant. "
            "Your goal is to answer the user's specific inquiry directly using the provided synthetic cohort metrics.\n"
            "Guidelines:\n"
            "- Direct Answer: Answer the user's inquiry directly in plain, friendly language. Do NOT use a rigid multi-section template.\n"
            "- Greetings / 'What is this': If the user says hello or asks what this is, briefly explain AttendSynth AI and the active cohort in 2-3 friendly sentences.\n"
            "- Analytical Questions: Provide 2-3 concise, bulleted insights citing exact numbers from the data.\n"
            "- Maximum Brevity: Keep the response very short and concise (strictly under 80-120 words) to avoid rate limits."
        )

        user_prompt = f"""Data Context:
- Active Students: {context['total_students']} | Overall Attendance: {context['average_attendance_pct']}% | Mean Engagement: {context['average_engagement_score']}/100
- Mean Marks: {context['average_marks']}% | Assignment Completion: {context['average_assignment_completion_pct']}% | Weekly LMS: {context['average_lms_logins_weekly']} visits
- Risk Breakdown: High={context['risk_distribution'].get('High', 0)}, Medium={context['risk_distribution'].get('Medium', 0)}, Low={context['risk_distribution'].get('Low', 0)}
- Trend Trajectories: {context['weekly_trajectories']} | Severe Attendance (<60%): {context['students_with_attendance_under_60pct']} students
- Incomplete Assignments (<50%): {context['students_with_assignments_under_50pct']} students | Low Participation (<40): {context['students_with_participation_under_40pct']} students
- Course Engagement Averages: {context['course_average_engagement']}

User Inquiry: "{user_query}"
Provide a concise, direct answer (under 100 words):"""

        try:
            from groq import Groq, RateLimitError, NotFoundError

            client = Groq(api_key=resolved_key)
            completion = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=cls.TEMPERATURE,
                max_tokens=cls.MAX_TOKENS,
            )

            msg = completion.choices[0].message
            response_content = (msg.content or "").strip()
            if not response_content:
                # In case reasoning tokens consumed the completion budget, fall back to smart local analysis
                response_content = cls.generate_heuristic_fallback(df, user_query)
            tokens_used = completion.usage.total_tokens if completion.usage else None

            return {
                "success": True,
                "status": "Groq Request Successful",
                "response": response_content,
                "model_used": target_model,
                "tokens_used": tokens_used,
                "is_fallback": False,
                "error": None,
                "retry_after": None,
            }
        except RateLimitError as e:
            retry_sec = None
            try:
                if hasattr(e, "response") and e.response is not None:
                    retry_sec = e.response.headers.get("retry-after")
            except Exception:
                pass

            err_msg = "Groq Free-Tier Rate Limit Reached (HTTP 429). Token quota per minute exceeded."
            if retry_sec:
                err_msg += f" Retry available in {retry_sec} seconds."

            return {
                "success": False,
                "status": "Groq Rate Limited",
                "response": cls.generate_heuristic_fallback(df, user_query),
                "is_fallback": True,
                "error": err_msg,
                "retry_after": retry_sec,
                "model_used": target_model,
                "tokens_used": None,
            }
        except NotFoundError as e:
            return {
                "success": False,
                "status": "Groq Temporarily Unavailable",
                "response": cls.generate_heuristic_fallback(df, user_query),
                "is_fallback": True,
                "error": f"Groq model '{target_model}' was not found on your account. Please check GROQ_MODEL in .env.",
                "model_used": target_model,
                "tokens_used": None,
            }
        except Exception as e:
            return {
                "success": False,
                "status": "Groq Temporarily Unavailable",
                "response": cls.generate_heuristic_fallback(df, user_query),
                "is_fallback": True,
                "error": f"Groq inference error ({type(e).__name__}): {str(e)}",
                "model_used": target_model,
                "tokens_used": None,
            }

    @classmethod
    def generate_heuristic_fallback(cls, df: pd.DataFrame, query: str) -> str:
        """
        Generates concise, query-targeted local statistical analysis based strictly on actual cohort metrics.
        Clearly labeled as Local Statistical Analysis.
        """
        context = cls.build_aggregate_context(df)
        if not context:
            return "No cohort records available for statistical analysis."

        q_lower = (query or "").lower().strip()
        tot = context["total_students"]
        high_risk = context["risk_distribution"].get("High", 0)
        med_risk = context["risk_distribution"].get("Medium", 0)
        low_risk = context["risk_distribution"].get("Low", 0)

        # 1. Greetings / What is this
        if any(w in q_lower for w in ["hi", "hello", "hey", "what is this", "what is attendsynth", "who are you", "help"]):
            return (
                f"### 👋 Welcome to AttendSynth AI\n\n"
                f"AttendSynth AI is an educational analytics platform generating privacy-safe synthetic student data for early warning systems.\n\n"
                f"- **Active Cohort**: **{tot} students** currently loaded in SQLite.\n"
                f"- **Overall Attendance**: **{context['average_attendance_pct']}%** (Mean Marks: **{context['average_marks']}%**).\n"
                f"- **Risk Profile**: **{high_risk} High-Risk**, {med_risk} Medium-Risk, {low_risk} Low-Risk.\n\n"
                f"Ask any specific question about course bottlenecks, disengagement drivers, or MTSS interventions!"
            )

        # 2. Risk / Early warning inquiries
        if any(w in q_lower for w in ["risk", "warning", "fail", "absent", "dropout", "drop", "ews"]):
            return (
                f"### 🚨 Early-Warning Risk Breakdown\n\n"
                f"- **High-Risk Threshold**: **{high_risk} of {tot} students ({round(high_risk/tot*100, 1) if tot else 0}%)** trigger critical alerts.\n"
                f"- **Primary Driver**: **{context['students_with_attendance_under_60pct']} students** suffer severe attendance deficits (<60%).\n"
                f"- **Coursework Bottlenecks**: **{context['students_with_assignments_under_50pct']} students** have incomplete assignments (<50%).\n"
                f"- **Trajectory Alert**: **{context['weekly_trajectories'].get('Declining', 0)} students** exhibit multi-week declining engagement."
            )

        # 3. Course-specific inquiries
        if any(w in q_lower for w in ["course", "subject", "curriculum", "class"]):
            courses = context.get("course_average_engagement", {})
            sorted_courses = sorted(courses.items(), key=lambda x: x[1])
            lowest = sorted_courses[0] if sorted_courses else ("N/A", 0)
            highest = sorted_courses[-1] if sorted_courses else ("N/A", 0)
            return (
                f"### 📚 Course Engagement Diagnostic\n\n"
                f"- **Lowest Engagement**: **{lowest[0]}** averages **{lowest[1]}/100**, indicating curriculum difficulty or disengagement.\n"
                f"- **Highest Engagement**: **{highest[0]}** leads with **{highest[1]}/100** engagement.\n"
                f"- **All Courses**: {', '.join([f'{k}: {v}/100' for k, v in sorted_courses])}."
            )

        # 4. Interventions / MTSS inquiries
        if any(w in q_lower for w in ["interven", "support", "action", "mtss", "plan", "recommend", "help student"]):
            return (
                f"### 🎯 Recommended Interventions\n\n"
                f"- **Tier 3 (Intensive)**: Mandatory 1-on-1 advisor outreach for the **{high_risk} high-risk students**.\n"
                f"- **Tier 2 (Targeted)**: Peer-tutoring study cohorts for the **{med_risk} moderate-risk students**.\n"
                f"- **Tier 1 (Universal)**: Automated LMS deadline alerts to curb the **{context['students_with_assignments_under_50pct']} coursework deficits**."
            )

        # 5. Default concise snapshot (under 75 words)
        return (
            f"### 📊 Cohort Analytics Diagnostic\n\n"
            f"- **Cohort Health**: {tot} students with **{context['average_attendance_pct']}%** attendance and **{context['average_marks']}%** average marks.\n"
            f"- **Vulnerability Alert**: **{high_risk} High-Risk** students ({context['students_with_attendance_under_60pct']} below 60% attendance).\n"
            f"- **Top Priority Action**: Trigger immediate advisor check-ins for the **{context['weekly_trajectories'].get('Declining', 0)} students** on declining trajectories."
        )
