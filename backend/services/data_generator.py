"""
Synthetic Student Engagement Data Generator Service for AttendSynth AI.
Generates realistic, longitudinally coherent student records and weekly time-series
using latent motivation factors, realistic educational covariance structures,
and unique stable student identities.
"""

import math
import uuid
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from faker import Faker
from .risk_engine import EarlyWarningEngine

DEFAULT_COURSES = [
    "CS101: Programming Fundamentals",
    "DS201: Data Science",
    "AI301: Artificial Intelligence",
    "DBMS202: Database Management Systems",
    "OS203: Operating Systems",
    "JAVA204: Object-Oriented Programming",
]


class SyntheticDataGenerator:
    """Generates synthetic student cohorts with realistic academic distributions."""

    def __init__(self, seed: int = 42):
        self.seed = int(seed)
        self.rng = np.random.RandomState(self.seed)
        self.fake = Faker()
        Faker.seed(self.seed)

    def generate_cohort(
        self,
        num_students: int = 250,
        num_weeks: int = 16,
        courses: Optional[List[str]] = None,
        semester: str = "Fall 2026",
        academic_year: str = "2026-2027",
        population_profile: str = "Balanced engagement",
        institution_id: Optional[str] = None,
        department_id: Optional[str] = None,
        cohort_id: Optional[str] = None,
        course_catalog: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generates:
        1. students_df: One row per student with composite metrics, engagement levels, risk scores.
        2. weekly_df: Full longitudinal time-series records for every student across every week.
        """
        if courses is None or len(courses) == 0:
            courses = DEFAULT_COURSES

        # Globally unique cohort prefix to ensure unique, non-colliding student IDs across all datasets
        if cohort_id:
            clean_id = cohort_id.replace("ds_", "").replace("-", "").replace("_", "").upper()
            prefix = clean_id[-6:] if len(clean_id) >= 6 else clean_id.ljust(6, "0")
        else:
            prefix = uuid.uuid4().hex[:6].upper()

        # 1. Sample latent motivation factor theta conditioned on population profile
        # Profiles: Balanced engagement, Mostly engaged, At-risk-heavy, Improving engagement, Declining engagement, Random mixed population
        if population_profile in ["Mostly engaged", "Mostly engaged students"]:
            theta = self.rng.normal(loc=0.9, scale=0.55, size=num_students)
        elif population_profile in ["At-risk-heavy", "At-risk-heavy population"]:
            theta = self.rng.normal(loc=-0.9, scale=0.65, size=num_students)
        elif population_profile in ["Improving engagement", "Improving"]:
            theta = self.rng.normal(loc=-0.3, scale=0.6, size=num_students)
        elif population_profile in ["Declining engagement", "Declining"]:
            theta = self.rng.normal(loc=0.4, scale=0.6, size=num_students)
        elif population_profile in ["Random mixed population", "Random distribution"]:
            # Mixture of high, medium, and low
            modes = self.rng.choice([-1.2, 0.0, 1.2], size=num_students, p=[0.3, 0.4, 0.3])
            theta = modes + self.rng.normal(loc=0.0, scale=0.4, size=num_students)
        else:  # Balanced engagement
            theta = self.rng.normal(loc=0.05, scale=0.75, size=num_students)

        # Clip theta to avoid mathematical runaways
        theta = np.clip(theta, -2.5, 2.5)

        # Map latent theta to percentile scale [0, 1] using standard normal CDF
        percentile = 0.5 * (1.0 + np.vectorize(math.erf)(theta / np.sqrt(2.0)))

        student_records = []
        weekly_records = []

        # Map courses to course_ids if course_catalog is provided
        course_map = {}
        if course_catalog:
            for c in course_catalog:
                key = c.get("code") or c.get("name")
                course_map[key] = c.get("id")

        for i in range(num_students):
            s_id = f"SYNTH-STU-{prefix}-{1001 + i}"
            name = self.fake.name()
            assigned_course = courses[i % len(courses)]
            assigned_course_id = course_map.get(assigned_course.split(":")[0].strip(), None)

            # Correlated student traits
            p_i = percentile[i]

            # Trajectory type based on population profile and latent motivation
            if population_profile in ["Improving engagement", "Improving"]:
                traj_chance = self.rng.rand()
                trend_type = "Improving" if traj_chance < 0.65 else ("Stable" if traj_chance < 0.9 else "Declining")
            elif population_profile in ["Declining engagement", "Declining"]:
                traj_chance = self.rng.rand()
                trend_type = "Declining" if traj_chance < 0.65 else ("Stable" if traj_chance < 0.9 else "Improving")
            else:
                if p_i < 0.25:
                    trend_type = self.rng.choice(["Declining", "Stable"], p=[0.6, 0.4])
                elif p_i > 0.75:
                    trend_type = self.rng.choice(["Improving", "Stable"], p=[0.4, 0.6])
                else:
                    trend_type = "Stable"

            # Baseline metrics with realistic covariance:
            # High attendance -> Higher LMS -> Higher Assignments -> Better Marks
            base_attendance = float(np.clip(45.0 + 52.0 * p_i + self.rng.normal(0, 4.0), 30.0, 100.0))
            base_lms_logins = float(np.clip(3.0 + 18.0 * p_i + self.rng.normal(0, 2.0), 1.0, 25.0))
            base_participation = float(np.clip(40.0 + 55.0 * p_i + self.rng.normal(0, 5.0), 25.0, 100.0))
            base_assignment = float(np.clip(40.0 + 56.0 * p_i + self.rng.normal(0, 5.0), 20.0, 100.0))
            base_marks = float(np.clip(40.0 + 55.0 * p_i + self.rng.normal(0, 6.0), 30.0, 100.0))

            # Late submissions inversely correlated with assignment completion
            late_submissions = int(np.clip(int((1.0 - p_i) * 6 + self.rng.poisson(0.5)), 0, 10))

            # Weekly time series generation
            weekly_scores = []
            for w in range(1, num_weeks + 1):
                progress = (w - 1) / max(1, num_weeks - 1)  # 0.0 to 1.0

                if trend_type == "Improving":
                    drift = progress * 14.0
                elif trend_type == "Declining":
                    drift = -progress * 16.0
                else:
                    drift = float(np.sin(w / 2.0) * 2.0)

                # Correlated weekly metrics with random perturbation
                w_noise = self.rng.normal(0, 3.0)
                w_att = float(np.clip(base_attendance + drift * 0.8 + w_noise, 15.0, 100.0))
                w_part = float(np.clip(base_participation + drift * 0.9 + self.rng.normal(0, 4.0), 15.0, 100.0))
                w_lms_min = float(np.clip((base_lms_logins * 6.5) + drift * 0.7 + self.rng.normal(0, 5.0), 10.0, 180.0))
                w_lms_logins = float(np.clip(base_lms_logins + (drift / 8.0) + self.rng.normal(0, 0.8), 0.5, 25.0))
                w_lms_score = float(np.clip((w_lms_logins / 20.0) * 100.0, 0.0, 100.0))
                w_assign_pct = float(np.clip(base_assignment + drift * 0.85 + self.rng.normal(0, 4.0), 10.0, 100.0))
                w_assign_count = int(np.round(w_assign_pct / 100.0 * 2.0))
                w_marks = float(np.clip(base_marks + drift * 0.7 + self.rng.normal(0, 4.0), 20.0, 100.0))

                # Transparent Engagement Formula (0.35 Att + 0.25 Part + 0.20 LMS + 0.20 Assign)
                w_eng = EarlyWarningEngine.calculate_engagement_score(
                    attendance_pct=w_att,
                    participation_score=w_part,
                    lms_score=w_lms_score,
                    assignment_completion_pct=w_assign_pct,
                )
                weekly_scores.append(w_eng)

                weekly_records.append({
                    "dataset_id": cohort_id,
                    "student_id": s_id,
                    "course_id": assigned_course_id,
                    "week_number": w,
                    "engagement_score": w_eng,
                    "attendance_pct": round(w_att, 1),
                    "lms_active_minutes": round(w_lms_min, 1),
                    "participation_score": round(w_part, 1),
                    "assignments_completed": w_assign_count,
                    "marks": round(w_marks, 1),
                })

            # Summary metrics across term
            term_attendance = float(np.clip(base_attendance + (drift * 0.5 if trend_type != "Stable" else 0.0), 20.0, 100.0))
            term_lms_logins = float(np.clip(base_lms_logins, 1.0, 25.0))
            term_part = float(np.clip(base_participation + (drift * 0.5 if trend_type != "Stable" else 0.0), 20.0, 100.0))
            term_assign = float(np.clip(base_assignment + (drift * 0.5 if trend_type != "Stable" else 0.0), 15.0, 100.0))
            term_marks = float(np.clip(base_marks + (drift * 0.4 if trend_type != "Stable" else 0.0), 25.0, 100.0))

            # Normalize LMS to 0-100 scale
            lms_score_norm = min(100.0, max(0.0, (term_lms_logins / 20.0) * 100.0))

            # Composite Engagement score
            engagement_score = EarlyWarningEngine.calculate_engagement_score(
                attendance_pct=term_attendance,
                participation_score=term_part,
                lms_score=lms_score_norm,
                assignment_completion_pct=term_assign,
            )

            # Engagement Tier (High >= 75, Medium >= 50, Low < 50)
            if engagement_score >= 75.0:
                engagement_level = "High"
            elif engagement_score >= 50.0:
                engagement_level = "Medium"
            else:
                engagement_level = "Low"

            # Risk calculation with transparent formulas and breakdown
            risk_eval = EarlyWarningEngine.calculate_student_risk(
                attendance_pct=term_attendance,
                assignment_completion_pct=term_assign,
                avg_marks=term_marks,
                participation_score=term_part,
                late_submissions=late_submissions,
                weekly_trajectory=trend_type,
                lms_logins_per_week=term_lms_logins,
            )

            student_records.append({
                "student_id": s_id,
                "dataset_id": cohort_id,
                "institution_id": institution_id,
                "course_id": assigned_course_id,
                "name": name,
                "course": assigned_course,
                "semester": semester,
                "academic_year": academic_year,
                "attendance_pct": round(term_attendance, 1),
                "lms_logins_per_week": round(term_lms_logins, 1),
                "participation_score": round(term_part, 1),
                "assignment_completion_pct": round(term_assign, 1),
                "avg_marks": round(term_marks, 1),
                "late_submissions": late_submissions,
                "engagement_score": engagement_score,
                "engagement_level": engagement_level,
                "risk_score": risk_eval["risk_score"],
                "risk_level": risk_eval["risk_level"],
                "weekly_trajectory": trend_type,
                "flagged_reasons": risk_eval["flagged_reasons"],
                "risk_breakdown": risk_eval["indicator_breakdown"],
                "support_recommendation": risk_eval["support_recommendation"],
                "weekly_history": weekly_scores,
            })

        students_df = pd.DataFrame(student_records)
        weekly_df = pd.DataFrame(weekly_records)
        return students_df, weekly_df


# Backward-compatible alias
DataGenerator = SyntheticDataGenerator
