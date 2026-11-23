"""
Core modules for AttendSynth AI.
"""

from core.data_generator import SyntheticDataGenerator, DEFAULT_COURSES
from core.risk_engine import EarlyWarningEngine
from core.analytics import DatasetAnalytics
from core.scenario_simulator import ScenarioSimulator
from core.ml_model import AcademicMLBenchmarker
from core.ai_insights import GroqInsightsEngine
from core.visualizations import (
    plot_engagement_distribution,
    plot_attendance_distribution,
    plot_risk_distribution,
    plot_course_comparison,
    plot_weekly_trends,
    plot_attendance_vs_participation,
    plot_single_student_trend,
    plot_confusion_matrix,
    plot_feature_importances,
    plot_scenario_comparison,
)

__all__ = [
    "SyntheticDataGenerator",
    "DEFAULT_COURSES",
    "EarlyWarningEngine",
    "DatasetAnalytics",
    "ScenarioSimulator",
    "AcademicMLBenchmarker",
    "GroqInsightsEngine",
    "plot_engagement_distribution",
    "plot_attendance_distribution",
    "plot_risk_distribution",
    "plot_course_comparison",
    "plot_weekly_trends",
    "plot_attendance_vs_participation",
    "plot_single_student_trend",
    "plot_confusion_matrix",
    "plot_feature_importances",
    "plot_scenario_comparison",
]
