"""
Synthetic Student Engagement Dataset Generator for AttendSynth AI.
Generates realistic, longitudinally coherent, and statistically correlated student records.
"""

import math
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from faker import Faker


DEFAULT_COURSES = [
    "CS101: Intro to Computer Science",
    "DS201: Data Science & Analytics",
    "MATH102: Linear Algebra & Calculus",
    "ENG105: Academic Writing & Research",
    "BIO110: Molecular Biology & Genetics",
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
        courses: List[str] = None,
        semester: str = "Fall 2026",
        population_profile: str = "Balanced engagement",
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generates:
        1. students_df: One row per student with summary metrics, engagement levels, risk scores.
        2. weekly_df: Longitudinal time-series record per student per week.
        """
        if courses is None or len(courses) == 0:
            courses = DEFAULT_COURSES

        # 1. Sample latent motivation factor theta conditioned on population profile
        if population_profile == "Mostly engaged students":
            theta = self.rng.normal(loc=0.9, scale=0.6, size=num_students)
        elif population_profile == "At-risk-heavy population":
            theta = self.rng.normal(loc=-0.8, scale=0.7, size=num_students)
        elif population_profile == "Random distribution":
            theta = self.rng.uniform(low=-1.8, high=1.8, size=num_students)
        else:  # Balanced engagement
            theta = self.rng.normal(loc=0.1, scale=0.8, size=num_students)

        # Clip theta to avoid mathematical runaways
        theta = np.clip(theta, -2.5, 2.5)

        # Standard normal CDF transform to map to percentile scale [0, 1]
        percentile = 0.5 * (1.0 + np.vectorize(math.erf)(theta / np.sqrt(2.0)))

        student_records = []
        weekly_records = []

        for i in range(num_students):
            s_id = f"STU-{1001 + i}"
            name = self.fake.name()
            course = courses[i % len(courses)]
            p = percentile[i]

            # 2. Correlated Core Indicators
            # Attendance %: strongly driven by p, with standard noise
            base_att = 40.0 + (p * 58.0) + self.rng.normal(0, 3.5)
            attendance_pct = float(np.clip(base_att, 25.0, 100.0))

            # Participation Score (0-100)
            base_part = 25.0 + (p * 68.0) + self.rng.normal(0, 5.0)
            participation_score = float(np.clip(base_part, 10.0, 100.0))

            # Assignment Completion % (0-100)
            base_assign = 30.0 + (p * 68.0) + self.rng.normal(0, 4.0)
            assignment_completion_pct = float(np.clip(base_assign, 15.0, 100.0))

            # LMS Logins per week (correlated with attendance & participation)
            lms_rate = 3.0 + (p * 18.0) + self.rng.normal(0, 2.0)
            lms_logins_per_week = float(np.clip(lms_rate, 1.0, 28.0))

            # Average Marks (0-100): correlated with assignments & participation
            base_marks = 35.0 + (p * 55.0) + self.rng.normal(0, 4.0)
            avg_marks = float(np.clip(base_marks, 30.0, 99.0))

            # Late submissions (negatively correlated with motivation)
            late_lambda = max(0.2, (1.0 - p) * 6.0)
            late_submissions = int(self.rng.poisson(lam=late_lambda))

            # 3. Composite Engagement Score (0 - 100)
            # Weights: Attendance (35%), Participation (25%), Assignment Completion (25%), LMS Active Rate (15%)
            lms_norm = min(100.0, (lms_logins_per_week / 18.0) * 100.0)
            engagement_score = (
                (0.35 * attendance_pct)
                + (0.25 * participation_score)
                + (0.25 * assignment_completion_pct)
                + (0.15 * lms_norm)
            )
            # Small penalty for late submissions
            engagement_score = float(np.clip(engagement_score - (late_submissions * 1.5), 5.0, 100.0))

            if engagement_score >= 75.0:
                engagement_level = "High"
            elif engagement_score >= 50.0:
                engagement_level = "Medium"
            else:
                engagement_level = "Low"

            # 4. Transparent Academic Risk Score (0 - 100)
            # Inverse of engagement with explicit penalties for critical triggers
            base_risk = 100.0 - engagement_score
            penalties = 0.0
            if attendance_pct < 60.0:
                penalties += 15.0
            if assignment_completion_pct < 50.0:
                penalties += 12.0
            if participation_score < 40.0:
                penalties += 10.0
            if avg_marks < 50.0:
                penalties += 12.0
            if late_submissions >= 4:
                penalties += 8.0

            risk_score = float(np.clip(base_risk * 0.7 + penalties, 0.0, 100.0))

            if risk_score >= 65.0:
                risk_level = "High"
            elif risk_score >= 35.0:
                risk_level = "Medium"
            else:
                risk_level = "Low"

            # 5. Longitudinal Weekly Trajectory
            # Profile determination
            if p > 0.65:
                trend_type = self.rng.choice(["Improving", "Stable", "Declining"], p=[0.35, 0.55, 0.10])
            elif p < 0.35:
                trend_type = self.rng.choice(["Improving", "Stable", "Declining"], p=[0.15, 0.30, 0.55])
            else:
                trend_type = self.rng.choice(["Improving", "Stable", "Declining"], p=[0.25, 0.55, 0.20])

            # Generate weekly engagement series
            weekly_scores = []
            cur_eng = engagement_score
            slope = 0.0
            if trend_type == "Improving":
                slope = self.rng.uniform(0.8, 2.0)
                cur_eng = max(20.0, engagement_score - (slope * num_weeks * 0.5))
            elif trend_type == "Declining":
                slope = -self.rng.uniform(0.8, 2.2)
                cur_eng = min(95.0, engagement_score - (slope * num_weeks * 0.5))

            for w in range(1, num_weeks + 1):
                cur_eng = cur_eng + slope + self.rng.normal(0, 1.8)
                cur_eng_clamped = float(np.clip(cur_eng, 5.0, 100.0))
                weekly_scores.append(round(cur_eng_clamped, 1))

                # Longitudinal record
                weekly_records.append({
                    "student_id": s_id,
                    "week_number": w,
                    "engagement_score": round(cur_eng_clamped, 1),
                    "attendance_pct": round(float(np.clip(attendance_pct + (slope * 0.7) + self.rng.normal(0, 2), 10, 100)), 1),
                    "lms_active_minutes": round(float(np.clip(lms_logins_per_week * 12.0 + (cur_eng_clamped * 0.3) + self.rng.normal(0, 8), 5, 240)), 1),
                    "assignments_completed": 1 if self.rng.rand() < (assignment_completion_pct / 100.0) else 0,
                })

            student_records.append({
                "student_id": s_id,
                "name": name,
                "course": course,
                "semester": semester,
                "attendance_pct": round(attendance_pct, 1),
                "lms_logins_per_week": round(lms_logins_per_week, 1),
                "participation_score": round(participation_score, 1),
                "assignment_completion_pct": round(assignment_completion_pct, 1),
                "avg_marks": round(avg_marks, 1),
                "late_submissions": late_submissions,
                "engagement_score": round(engagement_score, 1),
                "engagement_level": engagement_level,
                "risk_score": round(risk_score, 1),
                "risk_level": risk_level,
                "weekly_trajectory": trend_type,
                "weekly_history": weekly_scores,
            })

        students_df = pd.DataFrame(student_records)
        weekly_df = pd.DataFrame(weekly_records)
        return students_df, weekly_df
