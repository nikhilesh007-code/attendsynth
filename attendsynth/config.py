"""Configuration schemas, enums, and presets for AttendSynth AI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import datetime


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    TARDY = "TARDY"
    EXCUSED_ABSENCE = "EXCUSED_ABSENCE"
    UNEXCUSED_ABSENCE = "UNEXCUSED_ABSENCE"


class SubmissionStatus(str, Enum):
    ON_TIME = "ON_TIME"
    LATE = "LATE"
    MISSED = "MISSED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"


class InterventionType(str, Enum):
    NONE = "NONE"
    ATTENDANCE_NUDGE_SMS = "ATTENDANCE_NUDGE_SMS"
    COUNSELOR_CHECKIN = "COUNSELOR_CHECKIN"
    ACADEMIC_TUTORING = "ACADEMIC_TUTORING"
    FAMILY_WRAPAROUND = "FAMILY_WRAPAROUND"


class ArchetypeType(str, Enum):
    CONSISTENT_ACHIEVER = "CONSISTENT_ACHIEVER"
    GRADUAL_DISENGAGER = "GRADUAL_DISENGAGER"
    SPORADIC_ATTENDEE = "SPORADIC_ATTENDEE"
    LATE_SEMESTER_SLUMPER = "LATE_SEMESTER_SLUMPER"
    CHRONIC_ABSENTEE = "CHRONIC_ABSENTEE"
    INTERVENTION_RESPONDER = "INTERVENTION_RESPONDER"


@dataclass
class SchoolCalendarConfig:
    start_date: str = "2026-08-24"
    total_weeks: int = 16
    school_days_per_week: int = 5
    exam_weeks: List[int] = field(default_factory=lambda: [8, 16])
    holiday_weeks: List[int] = field(default_factory=lambda: [12])  # e.g., Fall/Thanksgiving Break
    district_name: str = "Horizon Metro Public Schools"
    school_names: List[str] = field(
        default_factory=lambda: [
            "Apex STEM Academy",
            "Lincoln Collegiate High",
            "Oak Creek Secondary School",
        ]
    )
    grade_levels: List[int] = field(default_factory=lambda: [9, 10, 11, 12])


@dataclass
class CohortConfig:
    cohort_id: str = "cohort_default"
    name: str = "Standard High School Cohort"
    num_students: int = 250
    random_seed: int = 42
    calendar: SchoolCalendarConfig = field(default_factory=SchoolCalendarConfig)
    
    # Archetype proportions (must sum to ~1.0)
    archetype_weights: Dict[ArchetypeType, float] = field(
        default_factory=lambda: {
            ArchetypeType.CONSISTENT_ACHIEVER: 0.45,
            ArchetypeType.GRADUAL_DISENGAGER: 0.20,
            ArchetypeType.SPORADIC_ATTENDEE: 0.15,
            ArchetypeType.LATE_SEMESTER_SLUMPER: 0.08,
            ArchetypeType.CHRONIC_ABSENTEE: 0.07,
            ArchetypeType.INTERVENTION_RESPONDER: 0.05,
        }
    )
    
    # Privacy / Differential Privacy parameters
    enable_dp_noise: bool = False
    dp_epsilon: float = 1.0  # Epsilon parameter for Laplace noise
    k_anonymity_threshold: int = 5
    
    # Early warning observation window (for model training features vs target)
    early_warning_obs_weeks: int = 6


class Presets:
    """Pre-configured cohort archetypes for quick simulation and benchmarking."""
    
    @staticmethod
    def standard_district(num_students: int = 300, seed: int = 42) -> CohortConfig:
        return CohortConfig(
            cohort_id="preset_standard_district",
            name="Standard District Benchmark",
            num_students=num_students,
            random_seed=seed,
            archetype_weights={
                ArchetypeType.CONSISTENT_ACHIEVER: 0.50,
                ArchetypeType.GRADUAL_DISENGAGER: 0.18,
                ArchetypeType.SPORADIC_ATTENDEE: 0.14,
                ArchetypeType.LATE_SEMESTER_SLUMPER: 0.08,
                ArchetypeType.CHRONIC_ABSENTEE: 0.06,
                ArchetypeType.INTERVENTION_RESPONDER: 0.04,
            },
        )
    
    @staticmethod
    def urban_at_risk(num_students: int = 300, seed: int = 42) -> CohortConfig:
        """High-risk cohort designed for testing early-warning sensitivity."""
        return CohortConfig(
            cohort_id="preset_urban_at_risk",
            name="Urban At-Risk Cohort (High Sensitivity Test)",
            num_students=num_students,
            random_seed=seed,
            archetype_weights={
                ArchetypeType.CONSISTENT_ACHIEVER: 0.25,
                ArchetypeType.GRADUAL_DISENGAGER: 0.30,
                ArchetypeType.SPORADIC_ATTENDEE: 0.20,
                ArchetypeType.LATE_SEMESTER_SLUMPER: 0.10,
                ArchetypeType.CHRONIC_ABSENTEE: 0.10,
                ArchetypeType.INTERVENTION_RESPONDER: 0.05,
            },
        )
    
    @staticmethod
    def hybrid_academy(num_students: int = 300, seed: int = 42) -> CohortConfig:
        """Blended learning academy with heavy reliance on LMS engagement."""
        return CohortConfig(
            cohort_id="preset_hybrid_academy",
            name="Blended / Hybrid Digital Academy",
            num_students=num_students,
            random_seed=seed,
            archetype_weights={
                ArchetypeType.CONSISTENT_ACHIEVER: 0.40,
                ArchetypeType.GRADUAL_DISENGAGER: 0.25,
                ArchetypeType.SPORADIC_ATTENDEE: 0.15,
                ArchetypeType.LATE_SEMESTER_SLUMPER: 0.10,
                ArchetypeType.CHRONIC_ABSENTEE: 0.05,
                ArchetypeType.INTERVENTION_RESPONDER: 0.05,
            },
        )

