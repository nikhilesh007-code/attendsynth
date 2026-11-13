"""Longitudinal synthetic data generation engine for student attendance and engagement."""

import datetime
import math
import random
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from attendsynth.config import (
    ArchetypeType,
    AttendanceStatus,
    CohortConfig,
    InterventionType,
    RiskLevel,
    SubmissionStatus,
)
from attendsynth.archetypes import (
    ArchetypeBehaviorProfile,
    DynamicTrajectoryModifier,
    get_archetype_profiles,
)

# Synthetic name banks to generate realistic, fully non-PII identities
FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Cameron",
    "Skyler", "Dakota", "Kai", "Quinn", "Rowan", "Reese", "Finley", "Emerson",
    "Harper", "Logan", "Peyton", "Kendall", "Hayden", "Sawyer", "Amari", "Micah",
    "Elena", "Mateo", "Priya", "Devon", "Aaliyah", "Zion", "Chen", "Mei",
    "Malik", "Fatima", "Darius", "Chloe", "Lucas", "Maya", "Tariq", "Siddharth",
]

LAST_NAMES = [
    "Rivera", "Chen", "Patel", "Washington", "Kowalski", "Kim", "O'Connor", "Santos",
    "Nakamura", "Al-Mansoor", "Novak", "Adeyemi", "Larsson", "Dubois", "Vargas", "Singh",
    "Bennett", "Mercer", "Sinclair", "Hawthorne", "Castillo", "Lindqvist", "Morales", "Zhang",
    "Brooks", "Adler", "Soto", "Mercado", "Vance", "Holloway", "Gomez", "Bauer",
]


class AttendSynthGenerator:
    """Generates synthetic student cohorts with realistic longitudinal engagement."""

    def __init__(self, config: Optional[CohortConfig] = None):
        self.config = config or CohortConfig()
        self.rng = np.random.RandomState(self.config.random_seed)
        random.seed(self.config.random_seed)
        self.profiles = get_archetype_profiles()

    def generate(self) -> Dict[str, Any]:
        """Generates the full cohort dataset including students, daily logs, and summary metrics."""
        students = self._generate_students()
        calendar_days = self._build_calendar()
        
        daily_records: List[Dict[str, Any]] = []
        student_summaries: List[Dict[str, Any]] = []

        for student in students:
            stu_records, stu_summary = self._generate_student_trajectory(student, calendar_days)
            daily_records.extend(stu_records)
            student_summaries.append(stu_summary)

        cohort_metadata = self._compute_cohort_metrics(student_summaries, len(calendar_days))

        return {
            "cohort_id": self.config.cohort_id,
            "cohort_name": self.config.name,
            "config": {
                "num_students": self.config.num_students,
                "total_weeks": self.config.calendar.total_weeks,
                "district_name": self.config.calendar.district_name,
                "random_seed": self.config.random_seed,
                "dp_noise_enabled": self.config.enable_dp_noise,
                "dp_epsilon": self.config.dp_epsilon,
            },
            "summary": cohort_metadata,
            "students": student_summaries,
            "daily_records": daily_records,
        }

    def _build_calendar(self) -> List[Dict[str, Any]]:
        """Constructs list of academic calendar instructional days (Mon-Fri)."""
        start = datetime.datetime.strptime(self.config.calendar.start_date, "%Y-%m-%d").date()
        days = []
        
        current_date = start
        total_weeks = self.config.calendar.total_weeks
        total_days = total_weeks * 7

        day_idx = 0
        for i in range(total_days):
            weekday = current_date.weekday()  # 0=Mon, ..., 4=Fri, 5=Sat, 6=Sun
            if weekday < 5:  # Instructional day
                week_num = (day_idx // 5) + 1
                is_exam = week_num in self.config.calendar.exam_weeks
                is_holiday = week_num in self.config.calendar.holiday_weeks
                
                # Check for assignments (typically due Wed or Fri)
                has_assignment = (weekday in [2, 4]) and not is_holiday
                # Quizzes occur on Fridays of non-exam, non-holiday weeks
                has_quiz = (weekday == 4) and not is_exam and not is_holiday

                days.append({
                    "day_index": day_idx,
                    "date": current_date.isoformat(),
                    "weekday": weekday,
                    "week_number": week_num,
                    "is_exam_week": is_exam,
                    "is_holiday_week": is_holiday,
                    "has_assignment": has_assignment,
                    "has_quiz": has_quiz,
                })
                day_idx += 1
            current_date += datetime.timedelta(days=1)
            
        return days

    def _generate_students(self) -> List[Dict[str, Any]]:
        """Samples student demographics and archetypes matching the distribution config."""
        archetypes = list(self.config.archetype_weights.keys())
        weights = [self.config.archetype_weights[a] for a in archetypes]
        total_weight = sum(weights)
        norm_weights = [w / total_weight for w in weights]

        selected_indices = self.rng.choice(
            len(archetypes), size=self.config.num_students, p=norm_weights
        )
        selected_archetypes = [archetypes[idx] for idx in selected_indices]

        students = []
        for i, arch in enumerate(selected_archetypes):
            stu_id = f"SYNTH_STU_{1000 + i + 1}"
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            school = random.choice(self.config.calendar.school_names)
            grade = int(random.choice(self.config.calendar.grade_levels))
            
            # Baseline GPA aligned realistically with archetype
            prof = self.profiles[arch]
            base_gpa = float(np.clip(
                (prof.quiz_score_mean / 25.0) - 0.2 + self.rng.normal(0, 0.25),
                1.5,
                4.0,
            ))

            students.append({
                "student_id": stu_id,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": f"{first_name} {last_name}",
                "school_name": school,
                "grade_level": grade,
                "archetype": arch,
                "archetype_label": prof.display_name,
                "baseline_gpa": round(base_gpa, 2),
                "socioeconomic_tier": random.choice(["TIER_1_STANDARD", "TIER_2_MODERATE", "TIER_3_SUPPORT_ELIGIBLE"]),
                "counselor_code": f"CNSLR_{101 + (i % 6)}",
            })
        return students

    def _generate_student_trajectory(
        self, student: Dict[str, Any], calendar_days: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Simulates longitudinal daily logs and computes composite risk metrics for one student."""
        archetype = student["archetype"]
        profile = self.profiles[archetype]
        total_weeks = self.config.calendar.total_weeks

        records = []
        days_present = 0
        days_tardy = 0
        unexcused_absences = 0
        excused_absences = 0
        total_lms_minutes = 0.0
        total_assignments_due = 0
        assignments_submitted = 0
        assignments_ontime = 0
        quiz_scores = []
        
        # Early warning detection tracking
        early_warning_trigger_day: Optional[int] = None
        rolling_absences = 0

        # Intervention week parameter for intervention responder
        intervention_week = 8

        for day in calendar_days:
            week = day["week_number"]
            weekday = day["weekday"]
            is_exam = day["is_exam_week"]
            is_holiday = day["is_holiday_week"]

            # Calculate dynamic trajectory modifiers
            mods = DynamicTrajectoryModifier.get_weekly_modifiers(
                archetype=archetype,
                week=week,
                total_weeks=total_weeks,
                is_exam_week=is_exam,
                is_holiday_week=is_holiday,
                intervention_week=intervention_week,
            )

            # Day-of-week attendance factor
            dow_multiplier = profile.dow_attendance_multipliers[weekday]
            
            # Adjusted attendance probability
            effective_att_prob = np.clip(
                (profile.base_attendance_prob + mods["attendance_delta"]) * dow_multiplier,
                0.15,
                0.99,
            )

            # Determine attendance status
            att_roll = self.rng.rand()
            if att_roll < effective_att_prob:
                # Student is attending: check if tardy
                effective_tardy_prob = np.clip(
                    profile.base_tardy_prob + mods["tardy_delta"], 0.01, 0.60
                )
                if self.rng.rand() < effective_tardy_prob:
                    status = AttendanceStatus.TARDY
                    days_tardy += 1
                else:
                    status = AttendanceStatus.PRESENT
                    days_present += 1
            else:
                # Student is absent: excused or unexcused
                if self.rng.rand() < profile.unexcused_ratio:
                    status = AttendanceStatus.UNEXCUSED_ABSENCE
                    unexcused_absences += 1
                    rolling_absences += 1
                else:
                    status = AttendanceStatus.EXCUSED_ABSENCE
                    excused_absences += 1
                    rolling_absences += 1

            # Determine LMS active minutes and logins
            # If absent, LMS engagement is typically reduced significantly
            if status in [AttendanceStatus.PRESENT, AttendanceStatus.TARDY]:
                att_factor = 1.0
            elif status == AttendanceStatus.EXCUSED_ABSENCE:
                att_factor = 0.45  # Sick/excused students check in occasionally
            else:
                att_factor = 0.15  # Unexcused absentees rarely log in

            lms_mean = max(5.0, profile.lms_minutes_mean * mods["lms_multiplier"] * att_factor)
            lms_minutes = float(np.clip(
                self.rng.normal(lms_mean, profile.lms_minutes_std),
                0.0,
                240.0,
            ))
            lms_logins = int(np.clip(
                self.rng.poisson(profile.lms_logins_mean * (lms_minutes / max(1.0, lms_mean))),
                0,
                15,
            ))
            total_lms_minutes += lms_minutes

            # Assignment submission logic
            sub_status: Optional[SubmissionStatus] = None
            if day["has_assignment"]:
                total_assignments_due += 1
                sub_prob = np.clip(
                    profile.assignment_submit_prob + (mods["attendance_delta"] * 0.5),
                    0.20,
                    0.99,
                )
                if self.rng.rand() < sub_prob:
                    assignments_submitted += 1
                    ontime_prob = np.clip(
                        profile.assignment_ontime_prob - mods["tardy_delta"], 0.30, 0.99
                    )
                    if self.rng.rand() < ontime_prob:
                        sub_status = SubmissionStatus.ON_TIME
                        assignments_ontime += 1
                    else:
                        sub_status = SubmissionStatus.LATE
                else:
                    sub_status = SubmissionStatus.MISSED

            # Quiz score logic
            day_quiz_score: Optional[float] = None
            if day["has_quiz"]:
                if status in [AttendanceStatus.PRESENT, AttendanceStatus.TARDY]:
                    raw_score = self.rng.normal(
                        profile.quiz_score_mean + mods["quiz_delta"], profile.quiz_score_std
                    )
                    day_quiz_score = round(float(np.clip(raw_score, 30.0, 100.0)), 1)
                    quiz_scores.append(day_quiz_score)
                else:
                    # Missed quiz yields 0 or make-up penalty later
                    day_quiz_score = 0.0
                    quiz_scores.append(0.0)

            # Daily Engagement Score (0-100 composite index)
            att_weight = 40.0 if status == AttendanceStatus.PRESENT else (
                25.0 if status == AttendanceStatus.TARDY else 0.0
            )
            lms_weight = min(35.0, (lms_minutes / 60.0) * 35.0)
            sub_weight = 25.0 if sub_status == SubmissionStatus.ON_TIME else (
                15.0 if sub_status == SubmissionStatus.LATE else (0.0 if sub_status == SubmissionStatus.MISSED else 20.0)
            )
            daily_engagement = round(float(np.clip(att_weight + lms_weight + sub_weight, 0.0, 100.0)), 1)

            # Check for Early Warning Trigger condition
            # EWS criteria: Cumulative absence > 10% after day 15 OR 3 unexcused absences within 10 days
            elapsed_days = day["day_index"] + 1
            if elapsed_days >= 15 and early_warning_trigger_day is None:
                total_absences = unexcused_absences + excused_absences
                if (total_absences / elapsed_days) >= 0.10 or unexcused_absences >= 3:
                    early_warning_trigger_day = elapsed_days

            record = {
                "student_id": student["student_id"],
                "date": day["date"],
                "day_index": day["day_index"],
                "week_number": week,
                "weekday": weekday,
                "attendance_status": status.value,
                "lms_active_minutes": round(lms_minutes, 1),
                "lms_logins": lms_logins,
                "assignment_due": day["has_assignment"],
                "submission_status": sub_status.value if sub_status else None,
                "quiz_given": day["has_quiz"],
                "quiz_score": day_quiz_score,
                "daily_engagement_score": daily_engagement,
            }
            records.append(record)

        # Compute full-term student summary metrics
        total_days = len(calendar_days)
        total_attended = days_present + days_tardy
        attendance_rate = total_attended / total_days
        absence_rate = (unexcused_absences + excused_absences) / total_days
        chronic_absenteeism = absence_rate >= 0.10  # Standard state/federal definition (>10% missed)

        mean_lms_minutes = round(total_lms_minutes / total_days, 1)
        sub_rate = round(assignments_submitted / max(1, total_assignments_due), 3)
        ontime_rate = round(assignments_ontime / max(1, assignments_submitted), 3)
        avg_quiz_score = round(float(np.mean(quiz_scores)) if quiz_scores else 75.0, 1)

        # Composite Early Warning Risk calculation
        # Risk factors: absence rate (45%), low LMS (25%), missing assignments (20%), low quiz (10%)
        risk_score = (
            min(1.0, absence_rate / 0.20) * 45.0 +
            max(0.0, (1.0 - min(1.0, mean_lms_minutes / 45.0))) * 25.0 +
            (1.0 - sub_rate) * 20.0 +
            max(0.0, (100.0 - avg_quiz_score) / 40.0) * 10.0
        )
        risk_score = round(float(np.clip(risk_score, 0.0, 100.0)), 1)

        if risk_score >= 65.0:
            risk_level = RiskLevel.CRITICAL
            recommended_intervention = InterventionType.FAMILY_WRAPAROUND
        elif risk_score >= 45.0:
            risk_level = RiskLevel.ELEVATED
            recommended_intervention = InterventionType.COUNSELOR_CHECKIN
        elif risk_score >= 25.0:
            risk_level = RiskLevel.MODERATE
            recommended_intervention = (
                InterventionType.ATTENDANCE_NUDGE_SMS
                if unexcused_absences >= 3
                else InterventionType.ACADEMIC_TUTORING
            )
        else:
            risk_level = RiskLevel.LOW
            recommended_intervention = InterventionType.NONE

        student_summary = {
            **student,
            "total_instructional_days": total_days,
            "days_present": days_present,
            "days_tardy": days_tardy,
            "unexcused_absences": unexcused_absences,
            "excused_absences": excused_absences,
            "attendance_rate": round(attendance_rate, 3),
            "absence_rate": round(absence_rate, 3),
            "chronic_absenteeism_flag": bool(chronic_absenteeism),
            "total_lms_minutes": round(total_lms_minutes, 1),
            "avg_daily_lms_minutes": mean_lms_minutes,
            "assignments_due": total_assignments_due,
            "assignments_submitted": assignments_submitted,
            "assignment_submission_rate": sub_rate,
            "assignment_ontime_rate": ontime_rate,
            "average_quiz_score": avg_quiz_score,
            "composite_risk_score": risk_score,
            "risk_level": risk_level.value,
            "early_warning_trigger_day": early_warning_trigger_day,
            "early_warning_trigger_week": (
                (early_warning_trigger_day // 5) + 1 if early_warning_trigger_day else None
            ),
            "recommended_intervention": recommended_intervention.value,
        }

        return records, student_summary

    def _compute_cohort_metrics(
        self, student_summaries: List[Dict[str, Any]], total_calendar_days: int
    ) -> Dict[str, Any]:
        """Calculates cohort-level aggregated KPIs and risk distributions."""
        n = len(student_summaries)
        if n == 0:
            return {}

        chronic_count = sum(1 for s in student_summaries if s["chronic_absenteeism_flag"])
        chronic_rate = round(chronic_count / n, 3)

        avg_attendance = round(float(np.mean([s["attendance_rate"] for s in student_summaries])), 3)
        avg_lms_min = round(float(np.mean([s["avg_daily_lms_minutes"] for s in student_summaries])), 1)
        avg_sub_rate = round(float(np.mean([s["assignment_submission_rate"] for s in student_summaries])), 3)
        avg_risk_score = round(float(np.mean([s["composite_risk_score"] for s in student_summaries])), 1)

        # Risk level distribution
        risk_counts = {r.value: 0 for r in RiskLevel}
        for s in student_summaries:
            risk_counts[s["risk_level"]] += 1

        # Archetype distribution
        arch_counts = {a.value: 0 for a in ArchetypeType}
        for s in student_summaries:
            arch_counts[s["archetype"]] += 1

        # Trigger week distribution for early-warning analysis
        flagged_students = [s for s in student_summaries if s["early_warning_trigger_week"] is not None]
        avg_lead_time_days = 0.0
        if flagged_students:
            avg_lead_time_days = round(
                float(np.mean([total_calendar_days - s["early_warning_trigger_day"] for s in flagged_students])),
                1,
            )

        return {
            "total_students": n,
            "total_school_days": total_calendar_days,
            "average_attendance_rate": avg_attendance,
            "chronic_absenteeism_count": chronic_count,
            "chronic_absenteeism_rate": chronic_rate,
            "average_daily_lms_minutes": avg_lms_min,
            "average_assignment_submission_rate": avg_sub_rate,
            "average_risk_score": avg_risk_score,
            "risk_distribution": risk_counts,
            "archetype_distribution": arch_counts,
            "early_warning_flagged_count": len(flagged_students),
            "early_warning_flagged_pct": round(len(flagged_students) / n, 3),
            "average_early_warning_lead_time_days": avg_lead_time_days,
        }
