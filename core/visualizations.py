"""
Interactive Plotly Visualization Library for AttendSynth AI.
Customized for the dark navy SaaS dashboard theme.
"""

from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


# Palette constants
PALETTE = {
    "bg_card": "rgba(19, 30, 54, 0.5)",
    "paper": "rgba(0, 0, 0, 0)",
    "grid": "rgba(51, 65, 85, 0.3)",
    "text": "#f8fafc",
    "text_muted": "#94a3b8",
    "blue": "#3b82f6",
    "cyan": "#38bdf8",
    "emerald": "#10b981",
    "amber": "#f59e0b",
    "rose": "#ef4444",
    "indigo": "#6366f1",
}


def apply_dark_layout(fig: go.Figure, title: str = "", height: int = 360) -> go.Figure:
    """Applies consistent dark navy SaaS layout styling to any Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(family="Plus Jakarta Sans", size=15, color=PALETTE["text"], weight="bold")),
        height=height,
        paper_bgcolor=PALETTE["paper"],
        plot_bgcolor=PALETTE["bg_card"],
        font=dict(family="Plus Jakarta Sans", color=PALETTE["text_muted"], size=12),
        margin=dict(l=20, r=20, t=45, b=25),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=PALETTE["text"]),
        ),
    )
    fig.update_xaxes(
        gridcolor=PALETTE["grid"],
        zerolinecolor=PALETTE["grid"],
        tickfont=dict(family="JetBrains Mono", size=10, color=PALETTE["text_muted"]),
    )
    fig.update_yaxes(
        gridcolor=PALETTE["grid"],
        zerolinecolor=PALETTE["grid"],
        tickfont=dict(family="JetBrains Mono", size=10, color=PALETTE["text_muted"]),
    )
    return fig


def plot_engagement_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram of student composite engagement scores."""
    if df.empty:
        return go.Figure()

    fig = px.histogram(
        df,
        x="engagement_score",
        nbins=25,
        color="engagement_level",
        color_discrete_map={"High": PALETTE["emerald"], "Medium": PALETTE["amber"], "Low": PALETTE["rose"]},
        opacity=0.85,
    )
    fig.update_traces(marker_line_width=1, marker_line_color="#0f172a")
    return apply_dark_layout(fig, title="Composite Engagement Score Distribution", height=320)


def plot_attendance_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram of student attendance rates with 60% chronic absence threshold line."""
    if df.empty:
        return go.Figure()

    fig = px.histogram(
        df,
        x="attendance_pct",
        nbins=25,
        color_discrete_sequence=[PALETTE["cyan"]],
        opacity=0.85,
    )
    fig.add_vline(
        x=60.0,
        line_width=2,
        line_dash="dash",
        line_color=PALETTE["rose"],
        annotation_text="Critical EWS Cutoff (60%)",
        annotation_position="top left",
        annotation_font=dict(color=PALETTE["rose"], size=10, family="JetBrains Mono"),
    )
    return apply_dark_layout(fig, title="Attendance Distribution Across Cohort (%)", height=320)


def plot_risk_distribution(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing Low, Medium, and High academic risk proportions."""
    if df.empty:
        return go.Figure()

    risk_counts = df["risk_level"].value_counts().reset_index()
    risk_counts.columns = ["risk_level", "count"]

    fig = px.pie(
        risk_counts,
        values="count",
        names="risk_level",
        hole=0.6,
        color="risk_level",
        color_discrete_map={"Low": PALETTE["emerald"], "Medium": PALETTE["amber"], "High": PALETTE["rose"]},
    )
    fig.update_traces(textposition="outside", textinfo="percent+label", textfont=dict(size=11, family="Plus Jakarta Sans"))
    return apply_dark_layout(fig, title="Cohort Academic Risk Tier Breakdown", height=320)


def plot_course_comparison(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart comparing Mean Engagement and Attendance across courses."""
    if df.empty:
        return go.Figure()

    grouped = df.groupby("course")[["attendance_pct", "engagement_score", "avg_marks"]].mean().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Attendance %",
        x=grouped["course"],
        y=grouped["attendance_pct"].round(1),
        marker_color=PALETTE["cyan"],
    ))
    fig.add_trace(go.Bar(
        name="Engagement Score",
        x=grouped["course"],
        y=grouped["engagement_score"].round(1),
        marker_color=PALETTE["blue"],
    ))
    fig.add_trace(go.Bar(
        name="Avg Marks",
        x=grouped["course"],
        y=grouped["avg_marks"].round(1),
        marker_color=PALETTE["emerald"],
    ))
    fig.update_layout(barmode="group")
    return apply_dark_layout(fig, title="Course-Wise Performance & Engagement Benchmarks", height=340)


def plot_weekly_trends(weekly_df: pd.DataFrame, max_lines: int = 30) -> go.Figure:
    """Longitudinal line trajectories over weeks with bold cohort average line."""
    if weekly_df.empty:
        return go.Figure()

    fig = go.Figure()

    # Sample student trajectories (faint lines)
    unique_students = weekly_df["student_id"].unique()
    sample_ids = unique_students[:max_lines]

    for sid in sample_ids:
        s_data = weekly_df[weekly_df["student_id"] == sid].sort_values("week_number")
        fig.add_trace(go.Scatter(
            x=s_data["week_number"],
            y=s_data["engagement_score"],
            mode="lines",
            line=dict(width=1, color="rgba(59, 130, 246, 0.18)"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Bold Cohort Mean Trendline
    cohort_mean = weekly_df.groupby("week_number")["engagement_score"].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=cohort_mean["week_number"],
        y=cohort_mean["engagement_score"].round(1),
        mode="lines+markers",
        name="Cohort Mean Engagement",
        line=dict(width=3.5, color=PALETTE["emerald"]),
        marker=dict(size=7, color=PALETTE["emerald"]),
    ))

    fig.update_xaxes(title="Instructional Week", dtick=1)
    fig.update_yaxes(title="Engagement Score (0-100)", range=[0, 105])
    return apply_dark_layout(fig, title="Longitudinal Weekly Engagement Trajectories", height=340)


def plot_attendance_vs_participation(df: pd.DataFrame) -> go.Figure:
    """Scatter plot: Attendance % vs Participation Score, colored by Risk Level."""
    if df.empty:
        return go.Figure()

    fig = px.scatter(
        df,
        x="attendance_pct",
        y="participation_score",
        color="risk_level",
        size="avg_marks",
        hover_data=["student_id", "name", "course", "engagement_score"],
        color_discrete_map={"Low": PALETTE["emerald"], "Medium": PALETTE["amber"], "High": PALETTE["rose"]},
        opacity=0.8,
    )
    fig.update_traces(marker=dict(line=dict(width=1, color="#0f172a")))
    fig.update_xaxes(title="Attendance Rate (%)")
    fig.update_yaxes(title="In-Class Participation Score (0-100)")
    return apply_dark_layout(fig, title="Attendance vs. Participation Correlation by Risk Level", height=360)


def plot_single_student_trend(weekly_records: List[float]) -> go.Figure:
    """Sparkline / trajectory line for a single student profile."""
    if not weekly_records:
        return go.Figure()

    weeks = list(range(1, len(weekly_records) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks,
        y=weekly_records,
        mode="lines+markers",
        line=dict(color=PALETTE["cyan"], width=3),
        marker=dict(size=6, color=PALETTE["blue"]),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.12)",
    ))
    fig.update_xaxes(title="Week", dtick=1)
    fig.update_yaxes(title="Engagement", range=[0, 105])
    return apply_dark_layout(fig, title="Individual Student Longitudinal History", height=240)


def plot_confusion_matrix(cm: List[List[int]]) -> go.Figure:
    """Heatmap of ML classification confusion matrix."""
    labels = ["Low/Medium Risk", "High Risk"]
    fig = px.imshow(
        cm,
        labels=dict(x="Predicted Risk Level", y="Actual Risk Label", color="Students"),
        x=labels,
        y=labels,
        text_auto=True,
        color_continuous_scale=[[0, "#0f172a"], [0.5, "#1e3a8a"], [1, "#3b82f6"]],
    )
    fig.update_coloraxes(showscale=False)
    return apply_dark_layout(fig, title="Machine Learning Confusion Matrix", height=300)


def plot_feature_importances(fi_list: List[Dict[str, Any]]) -> go.Figure:
    """Horizontal bar chart showing top predictive features in early warning ML."""
    if not fi_list:
        return go.Figure()

    fi_df = pd.DataFrame(fi_list).sort_values("percentage", ascending=True)
    clean_names = {
        "attendance_pct": "Attendance %",
        "participation_score": "In-Class Participation",
        "assignment_completion_pct": "Assignment Completion %",
        "lms_logins_per_week": "LMS Weekly Logins",
        "avg_marks": "Average Assessment Marks",
        "late_submissions": "Late Submissions Count",
    }
    fi_df["clean_feature"] = fi_df["feature"].map(lambda f: clean_names.get(f, f))

    fig = px.bar(
        fi_df,
        x="percentage",
        y="clean_feature",
        orientation="h",
        color="percentage",
        color_continuous_scale=[[0, "#38bdf8"], [1, "#3b82f6"]],
        text="percentage",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title="Importance Weight (%)", range=[0, max(50, fi_df['percentage'].max() + 8)])
    fig.update_yaxes(title="")
    return apply_dark_layout(fig, title="Predictive Signal Importance (Random Forest)", height=300)


def plot_scenario_comparison(baseline_summary: Dict[str, Any], sim_summary: Dict[str, Any]) -> go.Figure:
    """Bar chart comparing baseline vs simulated metrics."""
    metrics = ["Avg Attendance (%)", "Avg Engagement Score", "High-Risk Student Count"]
    base_vals = [
        baseline_summary.get("avg_attendance", 0),
        baseline_summary.get("avg_engagement", 0),
        baseline_summary.get("high_risk_count", 0),
    ]
    sim_vals = [
        sim_summary.get("sim_avg_attendance", 0),
        sim_summary.get("sim_avg_engagement", 0),
        sim_summary.get("sim_high_risk_count", 0),
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Baseline Dataset", x=metrics, y=base_vals, marker_color=PALETTE["blue"]))
    fig.add_trace(go.Bar(name="Simulated Outcome", x=metrics, y=sim_vals, marker_color=PALETTE["emerald"]))
    fig.update_layout(barmode="group")
    return apply_dark_layout(fig, title="Baseline vs. Simulated Policy Outcomes", height=340)
