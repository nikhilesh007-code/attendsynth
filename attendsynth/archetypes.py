"""Student behavioral archetypes and dynamic progression models for AttendSynth."""

from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np

from attendsynth.config import ArchetypeType, AttendanceStatus, SubmissionStatus


@dataclass
class ArchetypeBehaviorProfile:
    archetype: ArchetypeType
    display_name: str
    description: str
    
    # Base attendance metrics (Week 1 baseline)
    base_attendance_prob: float
    base_tardy_prob: float
    unexcused_ratio: float  # Fraction of absences that are unexcused
    
    # LMS daily metrics
    lms_minutes_mean: float
    lms_minutes_std: float
    lms_logins_mean: float
    
    # Academic & submission metrics
    assignment_submit_prob: float
    assignment_ontime_prob: float
    quiz_score_mean: float
    quiz_score_std: float
    
    # Day-of-week sensitivity: [Mon, Tue, Wed, Thu, Fri]
    dow_attendance_multipliers: Tuple[float, float, float, float, float]
    
    # Trajectory model function


StudentArchetype = ArchetypeBehaviorProfile


def get_archetype_profiles() -> Dict[ArchetypeType, ArchetypeBehaviorProfile]:
    return {
        ArchetypeType.CONSISTENT_ACHIEVER: ArchetypeBehaviorProfile(
            archetype=ArchetypeType.CONSISTENT_ACHIEVER,
            display_name="Consistent High Achiever",
            description="High baseline attendance and LMS engagement; resilient to academic slumps.",
            base_attendance_prob=0.97,
            base_tardy_prob=0.03,
            unexcused_ratio=0.15,
            lms_minutes_mean=75.0,
            lms_minutes_std=15.0,
            lms_logins_mean=3.8,
            assignment_submit_prob=0.98,
            assignment_ontime_prob=0.96,
            quiz_score_mean=88.0,
            quiz_score_std=6.5,
            dow_attendance_multipliers=(0.99, 1.0, 1.0, 1.0, 0.98),
        ),
        ArchetypeType.GRADUAL_DISENGAGER: ArchetypeBehaviorProfile(
            archetype=ArchetypeType.GRADUAL_DISENGAGER,
            display_name="Gradual Disengager (Early Warning Target)",
            description="Starts with solid engagement; LMS activity and tardiness deteriorate early, followed by severe attendance drops.",
            base_attendance_prob=0.93,
            base_tardy_prob=0.08,
            unexcused_ratio=0.55,
            lms_minutes_mean=58.0,
            lms_minutes_std=18.0,
            lms_logins_mean=2.8,
            assignment_submit_prob=0.91,
            assignment_ontime_prob=0.85,
            quiz_score_mean=77.0,
            quiz_score_std=9.0,
            dow_attendance_multipliers=(0.92, 1.0, 1.0, 0.98, 0.88),
        ),
        ArchetypeType.SPORADIC_ATTENDEE: ArchetypeBehaviorProfile(
            archetype=ArchetypeType.SPORADIC_ATTENDEE,
            display_name="Sporadic / High Variance Attendee",
            description="Attendance fluctuates heavily based on external barriers (transport, caretaking); sharp Monday/Friday drop-offs.",
            base_attendance_prob=0.83,
            base_tardy_prob=0.18,
            unexcused_ratio=0.50,
            lms_minutes_mean=42.0,
            lms_minutes_std=22.0,
            lms_logins_mean=2.1,
            assignment_submit_prob=0.80,
            assignment_ontime_prob=0.70,
            quiz_score_mean=71.0,
            quiz_score_std=12.0,
            dow_attendance_multipliers=(0.80, 1.02, 1.05, 0.98, 0.76),
        ),
        ArchetypeType.LATE_SEMESTER_SLUMPER: ArchetypeBehaviorProfile(
            archetype=ArchetypeType.LATE_SEMESTER_SLUMPER,
            display_name="Late-Semester Slumper",
            description="Maintains stable engagement through mid-semester, then experiences burnout or disengagement after midterm exams.",
            base_attendance_prob=0.94,
            base_tardy_prob=0.06,
            unexcused_ratio=0.45,
            lms_minutes_mean=62.0,
            lms_minutes_std=16.0,
            lms_logins_mean=3.0,
            assignment_submit_prob=0.92,
            assignment_ontime_prob=0.88,
            quiz_score_mean=81.0,
            quiz_score_std=8.0,
            dow_attendance_multipliers=(0.95, 1.0, 1.0, 0.98, 0.91),
        ),
        ArchetypeType.CHRONIC_ABSENTEE: ArchetypeBehaviorProfile(
            archetype=ArchetypeType.CHRONIC_ABSENTEE,
            display_name="Chronic Absentee",
            description="Consistently low attendance from early weeks, high unexcused absences, disengaged from digital platforms.",
            base_attendance_prob=0.72,
            base_tardy_prob=0.25,
            unexcused_ratio=0.75,
            lms_minutes_mean=24.0,
            lms_minutes_std=14.0,
            lms_logins_mean=1.2,
            assignment_submit_prob=0.60,
            assignment_ontime_prob=0.50,
            quiz_score_mean=60.0,
            quiz_score_std=14.0,
            dow_attendance_multipliers=(0.82, 0.98, 1.02, 0.95, 0.78),
        ),
        ArchetypeType.INTERVENTION_RESPONDER: ArchetypeBehaviorProfile(
            archetype=ArchetypeType.INTERVENTION_RESPONDER,
            display_name="Intervention Responder",
            description="Begins disengaging, but receives an early intervention (counselor or SMS alert) and exhibits positive recovery.",
            base_attendance_prob=0.91,
            base_tardy_prob=0.10,
            unexcused_ratio=0.50,
            lms_minutes_mean=55.0,
            lms_minutes_std=16.0,
            lms_logins_mean=2.6,
            assignment_submit_prob=0.88,
            assignment_ontime_prob=0.80,
            quiz_score_mean=74.0,
            quiz_score_std=9.5,
            dow_attendance_multipliers=(0.91, 1.0, 1.0, 0.98, 0.89),
        ),
    }


class DynamicTrajectoryModifier:
    """Calculates weekly temporal modifiers for each archetype."""

    @staticmethod
    def get_weekly_modifiers(
        archetype: ArchetypeType,
        week: int,
        total_weeks: int,
        is_exam_week: bool,
        is_holiday_week: bool,
        intervention_week: int = 8,
    ) -> Dict[str, float]:
        """Returns multipliers/addends for [attendance_prob, lms_time, quiz_score, tardy_rate]."""
        att_mod = 0.0
        tardy_mod = 0.0
        lms_mod = 1.0
        quiz_mod = 0.0

        if archetype == ArchetypeType.CONSISTENT_ACHIEVER:
            # Steady performance, slight bump during exam weeks
            if is_exam_week:
                lms_mod = 1.25
                att_mod = 0.01
            elif is_holiday_week:
                lms_mod = 0.45

        elif archetype == ArchetypeType.GRADUAL_DISENGAGER:
            # LMS minutes drop first (weeks 3-6), then attendance drops (weeks 5+)
            if week >= 3:
                lms_mod = max(0.25, 1.0 - (week - 2) * 0.065)
                tardy_mod = min(0.20, (week - 2) * 0.02)
            if week >= 5:
                att_mod = -min(0.35, (week - 4) * 0.035)
                quiz_mod = -min(18.0, (week - 4) * 1.5)

        elif archetype == ArchetypeType.SPORADIC_ATTENDEE:
            # Persistent variance; stress during exam weeks causes attendance dips
            if is_exam_week:
                att_mod = -0.08
                lms_mod = 1.10
                tardy_mod = 0.08
            elif is_holiday_week:
                lms_mod = 0.30

        elif archetype == ArchetypeType.LATE_SEMESTER_SLUMPER:
            # Stable until halfway through, then steep drop
            mid_point = total_weeks // 2
            if week > mid_point:
                decay_weeks = week - mid_point
                att_mod = -min(0.32, decay_weeks * 0.045)
                lms_mod = max(0.35, 1.0 - decay_weeks * 0.08)
                quiz_mod = -min(16.0, decay_weeks * 2.0)
                tardy_mod = min(0.18, decay_weeks * 0.025)

        elif archetype == ArchetypeType.CHRONIC_ABSENTEE:
            # Baseline low, deteriorates further towards end
            att_mod = -min(0.15, week * 0.01)
            lms_mod = max(0.40, 1.0 - week * 0.03)
            if is_exam_week:
                att_mod -= 0.05

        elif archetype == ArchetypeType.INTERVENTION_RESPONDER:
            # Disengages until intervention_week, then recovers
            if week < intervention_week:
                att_mod = -min(0.18, week * 0.025)
                lms_mod = max(0.55, 1.0 - week * 0.05)
                tardy_mod = min(0.12, week * 0.015)
            else:
                recovery_weeks = week - intervention_week + 1
                att_mod = min(0.04, -0.18 + recovery_weeks * 0.06)
                lms_mod = min(1.20, 0.55 + recovery_weeks * 0.12)
                tardy_mod = max(0.0, 0.12 - recovery_weeks * 0.03)
                quiz_mod = min(8.0, recovery_weeks * 1.8)

        return {
            "attendance_delta": att_mod,
            "tardy_delta": tardy_mod,
            "lms_multiplier": lms_mod,
            "quiz_delta": quiz_mod,
        }
