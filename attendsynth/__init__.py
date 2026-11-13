"""AttendSynth AI: Synthetic Student Engagement Generator.

A privacy-preserving synthetic data generation engine for modeling realistic student
attendance, LMS activity, and engagement patterns for early-warning predictive systems.
"""

__version__ = "1.0.0"

from attendsynth.config import CohortConfig, SchoolCalendarConfig, Presets
from attendsynth.generator import AttendSynthGenerator
from attendsynth.archetypes import ArchetypeType, StudentArchetype
from attendsynth.privacy import PrivacyAuditor, DifferentialPrivacyEngine
from attendsynth.metrics import FidelityEvaluator

__all__ = [
    "CohortConfig",
    "SchoolCalendarConfig",
    "Presets",
    "AttendSynthGenerator",
    "ArchetypeType",
    "StudentArchetype",
    "PrivacyAuditor",
    "DifferentialPrivacyEngine",
    "FidelityEvaluator",
]

