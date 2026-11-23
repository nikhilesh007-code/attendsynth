"""
AttendSynth AI – Main Application Router & Entrypoint.
Provides unified dark navy SaaS layout, shared session state, and multi-page routing.
"""

import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load environment variables (e.g., GROQ_API_KEY)
load_dotenv()

from styles.theme import apply_theme, render_brand_header
from core.data_generator import SyntheticDataGenerator, DEFAULT_COURSES
from core.views import (
    render_dashboard_view,
    render_generator_view,
    render_analytics_view,
    render_early_warning_view,
    render_groq_insights_view,
    render_simulator_view,
    render_ml_lab_view,
    render_export_view,
)


# Configure Streamlit Page Settings
st.set_page_config(
    page_title="AttendSynth AI - Synthetic Student Engagement",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Dark Navy SaaS Custom CSS
apply_theme()


def init_session_state():
    """Initializes persistent session state with a realistic default cohort so the app is never empty."""
    if "students_df" not in st.session_state or st.session_state["students_df"] is None:
        generator = SyntheticDataGenerator(seed=42)
        students_df, weekly_df = generator.generate_cohort(
            num_students=250,
            num_weeks=16,
            courses=DEFAULT_COURSES,
            semester="Fall 2026",
            population_profile="Balanced engagement",
        )
        st.session_state["students_df"] = students_df
        st.session_state["weekly_df"] = weekly_df
        st.session_state["config"] = {
            "num_students": 250,
            "num_weeks": 16,
            "courses": DEFAULT_COURSES,
            "semester": "Fall 2026",
            "population_profile": "Balanced engagement",
            "seed": 42,
        }

    if "groq_api_key" not in st.session_state:
        st.session_state["groq_api_key"] = os.environ.get("GROQ_API_KEY", "")

    if "current_nav" not in st.session_state:
        st.session_state["current_nav"] = "📊 Dashboard"


init_session_state()


# Sidebar Navigation & Quick Controls
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 0.65rem; padding: 0.5rem 0 1.25rem 0;">
            <div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #3b82f6, #38bdf8); display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
                🎓
            </div>
            <div>
                <div style="font-weight: 800; font-size: 1.15rem; color: #ffffff; letter-spacing: -0.02em;">AttendSynth AI</div>
                <div style="font-size: 0.72rem; color: #94a3b8; font-family: 'JetBrains Mono';">v2.0 • SaaS Edition</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_options = [
        "📊 Dashboard",
        "⚙️ Data Generator",
        "🔍 Student Analytics",
        "🚨 Early Warning System",
        "🤖 Groq AI Insights",
        "🔮 Scenario Simulator",
        "🧠 Machine Learning Lab",
        "📥 Export Data",
    ]

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state["current_nav"]) if st.session_state["current_nav"] in nav_options else 0,
        label_visibility="collapsed",
    )
    st.session_state["current_nav"] = selected_nav

    st.markdown("---")

    # Current Active Cohort Quick Status Pill
    df = st.session_state.get("students_df", pd.DataFrame())
    cfg = st.session_state.get("config", {})

    st.markdown(
        f"""
        <div style="background: rgba(19, 30, 54, 0.7); border: 1px solid #1e293b; border-radius: 12px; padding: 0.85rem; font-size: 0.78rem;">
            <div style="color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; margin-bottom: 0.4rem;">Active Synthetic Cohort</div>
            <div style="color: #ffffff; font-weight: 700; font-size: 0.92rem;">{len(df):,} Students</div>
            <div style="color: #38bdf8; font-family: 'JetBrains Mono'; font-size: 0.75rem;">{cfg.get('semester', 'Fall 2026')} • {cfg.get('num_weeks', 16)} Wks</div>
            <div style="color: #64748b; font-size: 0.72rem; margin-top: 0.25rem;">Profile: {cfg.get('population_profile', 'Balanced')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Groq API Status Indicator in Sidebar
    groq_configured = bool(st.session_state.get("groq_api_key", "").strip() or os.environ.get("GROQ_API_KEY", "").strip())
    if groq_configured:
        st.markdown('<span class="pill pill-emerald" style="width: 100%; justify-content: center;">⚡ Groq API Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill pill-amber" style="width: 100%; justify-content: center;">⚠️ Groq Key Not Set</span>', unsafe_allow_html=True)


# Render Top SaaS Header
render_brand_header()

# Page Routing
current_page = st.session_state["current_nav"]
students_df = st.session_state.get("students_df", pd.DataFrame())
weekly_df = st.session_state.get("weekly_df", pd.DataFrame())

if current_page == "📊 Dashboard":
    render_dashboard_view(students_df, weekly_df)
elif current_page == "⚙️ Data Generator":
    render_generator_view(students_df)
elif current_page == "🔍 Student Analytics":
    render_analytics_view(students_df)
elif current_page == "🚨 Early Warning System":
    render_early_warning_view(students_df)
elif current_page == "🤖 Groq AI Insights":
    render_groq_insights_view(students_df)
elif current_page == "🔮 Scenario Simulator":
    render_simulator_view(students_df)
elif current_page == "🧠 Machine Learning Lab":
    render_ml_lab_view(students_df)
elif current_page == "📥 Export Data":
    render_export_view(students_df, weekly_df)
