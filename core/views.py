"""
Modular View Components for AttendSynth AI Pages.
Contains the rendering logic for all 8 application pages.
"""

import os
import streamlit as st
import pandas as pd
from styles.theme import render_kpi
from core.data_generator import SyntheticDataGenerator, DEFAULT_COURSES
from core.analytics import DatasetAnalytics
from core.risk_engine import EarlyWarningEngine
from core.ai_insights import GroqInsightsEngine
from core.scenario_simulator import ScenarioSimulator
from core.ml_model import AcademicMLBenchmarker
import core.visualizations as viz


def render_dashboard_view(students_df: pd.DataFrame, weekly_df: pd.DataFrame):
    """Page 1: Executive Overview Dashboard."""
    st.markdown("### 📊 Executive Overview Dashboard")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Real-time statistical indicators and cohort engagement benchmarks.</p>",
        unsafe_allow_html=True,
    )

    kpis = DatasetAnalytics.compute_summary_kpis(students_df)

    # Top KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_kpi("Total Students", f"{kpis['total_students']:,}", "Active Synthetic Cohort", "100% Synthetic", "blue"), unsafe_allow_html=True)
    with col2:
        att_pill = "emerald" if kpis['avg_attendance'] >= 80 else ("amber" if kpis['avg_attendance'] >= 65 else "rose")
        st.markdown(render_kpi("Mean Attendance", f"{kpis['avg_attendance']}%", "Across Semester Term", "Term Avg", att_pill), unsafe_allow_html=True)
    with col3:
        eng_pill = "emerald" if kpis['avg_engagement'] >= 70 else ("amber" if kpis['avg_engagement'] >= 50 else "rose")
        st.markdown(render_kpi("Engagement Index", f"{kpis['avg_engagement']}", "Composite 0-100 Score", "Index", eng_pill), unsafe_allow_html=True)
    with col4:
        st.markdown(render_kpi("High-Risk Students", f"{kpis['high_risk_count']}", f"{kpis['high_risk_pct']}% of total population", "EWS Alert", "rose"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sub-KPI Row
    scol1, scol2, scol3, scol4 = st.columns(4)
    with scol1:
        st.markdown(render_kpi("High Engagement", f"{kpis['high_engagement_count']}", "Score ≥ 75.0", "Tier 1", "emerald"), unsafe_allow_html=True)
    with scol2:
        st.markdown(render_kpi("Medium Engagement", f"{kpis['medium_engagement_count']}", "Score 50.0 - 74.9", "Tier 2", "cyan"), unsafe_allow_html=True)
    with scol3:
        st.markdown(render_kpi("Low Engagement", f"{kpis['low_engagement_count']}", "Score < 50.0", "Tier 3", "amber"), unsafe_allow_html=True)
    with scol4:
        st.markdown(render_kpi("Assignment Rate", f"{kpis['avg_assignment_completion']}%", "Submitted On-Time / Total", "Submissions", "blue"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 1 Charts: Distributions
    c1, c2, c3 = st.columns([1.2, 1.2, 1])
    with c1:
        st.plotly_chart(viz.plot_engagement_distribution(students_df), use_container_width=True)
    with c2:
        st.plotly_chart(viz.plot_attendance_distribution(students_df), use_container_width=True)
    with c3:
        st.plotly_chart(viz.plot_risk_distribution(students_df), use_container_width=True)

    # Row 2 Charts: Longitudinal & Course Comparisons
    c4, c5 = st.columns([1.3, 1.1])
    with c4:
        st.plotly_chart(viz.plot_weekly_trends(weekly_df), use_container_width=True)
    with c5:
        st.plotly_chart(viz.plot_course_comparison(students_df), use_container_width=True)

    # Recent Synthetic Student Table
    st.markdown("#### 📋 Recent Synthetic Student Records (Live Cohort Sample)")
    display_cols = [
        "student_id", "name", "course", "attendance_pct", "participation_score",
        "assignment_completion_pct", "avg_marks", "engagement_score", "engagement_level", "risk_level"
    ]
    st.dataframe(students_df[display_cols].head(20), use_container_width=True, hide_index=True)


def render_generator_view(students_df: pd.DataFrame):
    """Page 2: Synthetic Data Generator Studio."""
    st.markdown("### ⚙️ Synthetic Data Generator Studio")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Configure population sizes, instructional terms, behavioral archetypes, and random seeds to synthesize realistic academic cohorts.</p>",
        unsafe_allow_html=True,
    )

    with st.form("generator_form"):
        st.markdown("##### 1. Cohort & Term Configuration")
        col1, col2, col3 = st.columns(3)
        with col1:
            student_count = st.selectbox(
                "Number of Students",
                options=[50, 100, 250, 500, 1000, 2000],
                index=2,
                help="Total fictional student identities and time series to generate.",
            )
        with col2:
            week_count = st.selectbox(
                "Number of Instructional Weeks",
                options=[4, 8, 12, 16],
                index=3,
                help="Duration of the longitudinal academic semester.",
            )
        with col3:
            semester = st.selectbox(
                "Academic Semester",
                options=["Fall 2026", "Spring 2026", "Summer 2026", "Fall 2025"],
                index=0,
            )

        st.markdown("##### 2. Course Catalog & Population Behavioral Profiles")
        col4, col5 = st.columns(2)
        with col4:
            selected_courses = st.multiselect(
                "Enrolled Academic Courses",
                options=DEFAULT_COURSES,
                default=DEFAULT_COURSES,
            )
            if not selected_courses:
                selected_courses = DEFAULT_COURSES
        with col5:
            population_profile = st.selectbox(
                "Population Behavioral Profile",
                options=[
                    "Balanced engagement",
                    "Mostly engaged students",
                    "At-risk-heavy population",
                    "Random distribution",
                ],
                index=0,
            )

        st.markdown("##### 3. Seed & Reproducibility")
        col6, col7 = st.columns([1, 2])
        with col6:
            random_seed = st.number_input("Random Seed", min_value=1, max_value=999999, value=42, step=1)
        with col7:
            st.info("💡 attendSynth AI uses correlated multivariate statistical models to ensure lower attendance correlates with higher academic risk, lower assignment completion, and realistic LMS logins.")

        submitted = st.form_submit_button("⚡ Synthesize & Load New Cohort", use_container_width=True)

    if submitted:
        with st.spinner(f"Synthesizing {student_count} student records across {week_count} instructional weeks..."):
            generator = SyntheticDataGenerator(seed=random_seed)
            new_students_df, new_weekly_df = generator.generate_cohort(
                num_students=student_count,
                num_weeks=week_count,
                courses=selected_courses,
                semester=semester,
                population_profile=population_profile,
            )
            st.session_state["students_df"] = new_students_df
            st.session_state["weekly_df"] = new_weekly_df
            st.session_state["config"] = {
                "num_students": student_count,
                "num_weeks": week_count,
                "courses": selected_courses,
                "semester": semester,
                "population_profile": population_profile,
                "seed": random_seed,
            }
            st.success(f"✓ Successfully synthesized and committed {student_count:,} student records ({len(new_weekly_df):,} longitudinal weekly records)!")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📈 Active Cohort Snapshot")
    st.dataframe(students_df.head(15), use_container_width=True, hide_index=True)


def render_analytics_view(students_df: pd.DataFrame):
    """Page 3: Student Analytics & Deep-Dive Explorer."""
    st.markdown("### 🔍 Student Analytics & Deep-Dive Explorer")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Filter, search, inspect individual student trajectories, and compare academic metrics side-by-side.</p>",
        unsafe_allow_html=True,
    )

    fcol1, fcol2, fcol3, fcol4 = st.columns([1.5, 1.2, 1, 1])
    with fcol1:
        search_query = st.text_input("🔎 Search Student by Name or ID", placeholder="e.g. STU-1012 or Rivera")
    with fcol2:
        course_filter = st.selectbox("Filter Course", options=["All Courses"] + list(students_df["course"].unique()))
    with fcol3:
        eng_filter = st.selectbox("Engagement Tier", options=["All", "High", "Medium", "Low"])
    with fcol4:
        risk_filter = st.selectbox("Risk Level", options=["All", "Low", "Medium", "High"])

    filtered_df = students_df.copy()
    if search_query:
        q = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(q) | filtered_df["student_id"].str.lower().str.contains(q)
        ]
    if course_filter != "All Courses":
        filtered_df = filtered_df[filtered_df["course"] == course_filter]
    if eng_filter != "All":
        filtered_df = filtered_df[filtered_df["engagement_level"] == eng_filter]
    if risk_filter != "All":
        filtered_df = filtered_df[filtered_df["risk_level"] == risk_filter]

    st.markdown(f"**Showing {len(filtered_df):,} of {len(students_df):,} students**")

    st.dataframe(
        filtered_df[[
            "student_id", "name", "course", "attendance_pct", "participation_score",
            "assignment_completion_pct", "avg_marks", "engagement_score", "engagement_level", "risk_level", "weekly_trajectory"
        ]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["👤 Single Student Inspector", "⚖️ Compare Two Students", "🌌 Multidimensional Correlation"])

    with tab1:
        if not filtered_df.empty:
            student_options = filtered_df["student_id"] + " - " + filtered_df["name"]
            selected_student_str = st.selectbox("Select Student to Inspect", options=student_options)
            sel_id = selected_student_str.split(" - ")[0]
            s = students_df[students_df["student_id"] == sel_id].iloc[0]

            icol1, icol2, icol3, icol4, icol5 = st.columns(5)
            with icol1:
                st.markdown(render_kpi("Attendance", f"{s['attendance_pct']}%", f"{s['course']}", "Telemetry", "cyan"), unsafe_allow_html=True)
            with icol2:
                st.markdown(render_kpi("Participation", f"{s['participation_score']}", "In-Class Engagement", "Score", "blue"), unsafe_allow_html=True)
            with icol3:
                st.markdown(render_kpi("Assignments", f"{s['assignment_completion_pct']}%", f"{s['late_submissions']} Late Submissions", "Homework", "amber"), unsafe_allow_html=True)
            with icol4:
                st.markdown(render_kpi("Engagement Index", f"{s['engagement_score']}", f"Level: {s['engagement_level']}", s['engagement_level'], "emerald" if s['engagement_level']=='High' else 'amber'), unsafe_allow_html=True)
            with icol5:
                st.markdown(render_kpi("Risk Score", f"{s['risk_score']}", f"Classification: {s['risk_level']}", s['risk_level'], "rose" if s['risk_level']=='High' else 'emerald'), unsafe_allow_html=True)

            st.plotly_chart(viz.plot_single_student_trend(s["weekly_history"]), use_container_width=True)
        else:
            st.info("No matching students found with current filters.")

    with tab2:
        all_options = students_df["student_id"] + " - " + students_df["name"]
        cmp_col1, cmp_col2 = st.columns(2)
        with cmp_col1:
            stu_a_str = st.selectbox("Select Student A", options=all_options, index=0)
            s_a = students_df[students_df["student_id"] == stu_a_str.split(" - ")[0]].iloc[0]
            st.markdown(
                f"""
                <div class="kpi-card">
                    <h4 style="margin: 0; color: #38bdf8;">{s_a['name']} ({s_a['student_id']})</h4>
                    <p style="color: #94a3b8; font-size: 0.8rem; margin: 0.2rem 0 1rem 0;">{s_a['course']}</p>
                    <p><b>Attendance:</b> {s_a['attendance_pct']}%</p>
                    <p><b>Participation:</b> {s_a['participation_score']} / 100</p>
                    <p><b>Assignment Completion:</b> {s_a['assignment_completion_pct']}%</p>
                    <p><b>Average Marks:</b> {s_a['avg_marks']}%</p>
                    <p><b>LMS Logins/Wk:</b> {s_a['lms_logins_per_week']}</p>
                    <p><b>Engagement Index:</b> <span class="pill pill-blue">{s_a['engagement_score']} ({s_a['engagement_level']})</span></p>
                    <p><b>Risk Status:</b> <span class="pill pill-rose">{s_a['risk_score']} ({s_a['risk_level']})</span></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(viz.plot_single_student_trend(s_a["weekly_history"]), use_container_width=True)

        with cmp_col2:
            stu_b_str = st.selectbox("Select Student B", options=all_options, index=min(1, len(all_options) - 1))
            s_b = students_df[students_df["student_id"] == stu_b_str.split(" - ")[0]].iloc[0]
            st.markdown(
                f"""
                <div class="kpi-card">
                    <h4 style="margin: 0; color: #38bdf8;">{s_b['name']} ({s_b['student_id']})</h4>
                    <p style="color: #94a3b8; font-size: 0.8rem; margin: 0.2rem 0 1rem 0;">{s_b['course']}</p>
                    <p><b>Attendance:</b> {s_b['attendance_pct']}%</p>
                    <p><b>Participation:</b> {s_b['participation_score']} / 100</p>
                    <p><b>Assignment Completion:</b> {s_b['assignment_completion_pct']}%</p>
                    <p><b>Average Marks:</b> {s_b['avg_marks']}%</p>
                    <p><b>LMS Logins/Wk:</b> {s_b['lms_logins_per_week']}</p>
                    <p><b>Engagement Index:</b> <span class="pill pill-blue">{s_b['engagement_score']} ({s_b['engagement_level']})</span></p>
                    <p><b>Risk Status:</b> <span class="pill pill-rose">{s_b['risk_score']} ({s_b['risk_level']})</span></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(viz.plot_single_student_trend(s_b["weekly_history"]), use_container_width=True)

    with tab3:
        st.plotly_chart(viz.plot_attendance_vs_participation(students_df), use_container_width=True)


def render_early_warning_view(students_df: pd.DataFrame):
    """Page 4: Transparent Early Warning System."""
    st.markdown("### 🚨 Transparent Early Warning System (EWS)")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Rule-based early-intervention triage identifying students requiring timely pedagogical or counseling support.</p>",
        unsafe_allow_html=True,
    )

    ews_df = EarlyWarningEngine.evaluate_cohort(students_df)
    flagged_students = ews_df[ews_df["is_flagged"]].sort_values("ews_risk_score", ascending=False)
    high_risk_flagged = ews_df[ews_df["ews_risk_level"] == "High"]

    ecol1, ecol2, ecol3, ecol4 = st.columns(4)
    with ecol1:
        st.markdown(render_kpi("Flagged Students", f"{len(flagged_students)}", f"{(len(flagged_students)/len(students_df)*100):.1f}% of Cohort", "Action Needed", "rose"), unsafe_allow_html=True)
    with ecol2:
        st.markdown(render_kpi("Critical Tier (High)", f"{len(high_risk_flagged)}", "Immediate Support Required", "Tier 3", "rose"), unsafe_allow_html=True)
    with ecol3:
        att_under_60 = (students_df["attendance_pct"] < 60.0).sum()
        st.markdown(render_kpi("Attendance Crises", f"{att_under_60}", "Attendance < 60%", "<60% Attn", "amber"), unsafe_allow_html=True)
    with ecol4:
        declining_count = (students_df["weekly_trajectory"] == "Declining").sum()
        st.markdown(render_kpi("Declining Trajectories", f"{declining_count}", "Multi-Week Decay", "Longitudinal", "amber"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass-container" style="border-left: 4px solid #f59e0b;">
            <div style="font-weight: 700; color: #fbbf24; margin-bottom: 0.35rem; font-size: 0.95rem;">
                ⚖️ Transparent Rule-Based Early Warning Policy
            </div>
            <div style="font-size: 0.84rem; color: #94a3b8; line-height: 1.5;">
                Students are flagged using deterministic, verifiable institutional thresholds:
                <b>(1)</b> Attendance &lt; 60%, <b>(2)</b> Classroom Participation &lt; 40%, 
                <b>(3)</b> Assignment Completion &lt; 50%, <b>(4)</b> Assessment Average &lt; 50%, 
                <b>(5)</b> Chronic Late Submissions (&ge; 4), and <b>(6)</b> Longitudinal Multi-Week Engagement Decay.
                <br><em>Disclaimer: These transparent indicators identify priority support candidates and do not claim causal predictive certainty.</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🚨 Prioritized Support Roster")
    st.markdown("<p style='font-size: 0.8rem; color: #64748b;'>Ordered by calculated EWS risk score. Expand rows to review actionable intervention strategies.</p>", unsafe_allow_html=True)

    for idx, row in flagged_students.head(15).iterrows():
        with st.expander(f"{row['student_id']} - {row['name']} | Risk: {row['ews_risk_score']} ({row['ews_risk_level']}) | {row['course']}"):
            rcol1, rcol2 = st.columns([1, 1.2])
            with rcol1:
                st.markdown(f"**Attendance:** {row['attendance_pct']}% | **Participation:** {row['participation_score']}")
                st.markdown(f"**Assignments Completed:** {row['assignment_completion_pct']}% | **Late Work:** {row['late_submissions']}")
                st.markdown(f"**Assessment Marks:** {row['avg_marks']}% | **Trajectory:** {row['weekly_trajectory']}")
                st.markdown("##### ⚠️ Triggered Early Warning Rules:")
                for reason in row['flag_reasons']:
                    st.markdown(f"- 🔴 `{reason}`")
            with rcol2:
                st.markdown("##### 🎯 Recommended Multi-Tiered Support Action:")
                for action in row['suggested_actions']:
                    st.markdown(f"- 💡 **{action}**")


def render_groq_insights_view(students_df: pd.DataFrame):
    """Page 5: Groq AI Insights."""
    st.markdown("### 🤖 Groq AI Education Analytics Co-Pilot")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Ultra-fast pedagogical diagnostics and MTSS intervention planning powered by Groq LPU inference (Llama 3.3 70B).</p>",
        unsafe_allow_html=True,
    )

    groq_configured = bool(st.session_state.get("groq_api_key", "").strip() or os.environ.get("GROQ_API_KEY", "").strip())
    with st.expander("🔑 Groq API Key Configuration & Status", expanded=not groq_configured):
        st.markdown(
            """
            Groq provides ultra-fast LLM inference at zero or low cost.
            1. Obtain a free API key at **[console.groq.com/keys](https://console.groq.com/keys)**.
            2. Paste your key below or save it as `GROQ_API_KEY` in your `.env` file.
            """
        )
        key_input = st.text_input(
            "Groq API Key",
            value=st.session_state.get("groq_api_key", ""),
            type="password",
            placeholder="gsk_...",
        )
        if st.button("Save API Key to Session"):
            st.session_state["groq_api_key"] = key_input.strip()
            st.success("✓ Groq API Key saved for this session!")
            st.rerun()

    mcol1, mcol2 = st.columns([1, 1])
    with mcol1:
        model_choice = st.selectbox(
            "Select Groq Model",
            options=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
            index=0,
        )
    with mcol2:
        st.markdown(
            """
            <div style="padding-top: 1.5rem;">
                <span class="pill pill-blue">Zero-PII Compliance</span>
                <span style="font-size: 0.78rem; color: #94a3b8; margin-left: 0.5rem;">Only aggregate statistics are sent.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("##### 💡 Quick Analytical Questions")
    pcol1, pcol2, pcol3 = st.columns(3)
    pcol4, pcol5, pcol6 = st.columns(3)

    query_to_run = None
    with pcol1:
        if st.button("📉 Why is engagement dropping?", use_container_width=True):
            query_to_run = "Why are students showing disengagement, and what are the primary root causes in this cohort?"
    with pcol2:
        if st.button("🗓️ Major Attendance Patterns", use_container_width=True):
            query_to_run = "Analyze the major attendance patterns and identify which student groups are most at risk of chronic absenteeism."
    with pcol3:
        if st.button("⚖️ Most Important Factors", use_container_width=True):
            query_to_run = "Which engagement factors (attendance vs assignments vs participation) appear most critical to academic success?"
    with pcol4:
        if st.button("🎯 Intervention Strategies", use_container_width=True):
            query_to_run = "What specific Multi-Tiered System of Supports (MTSS) interventions could improve attendance and assignment completion?"
    with pcol5:
        if st.button("📋 Executive Cohort Summary", use_container_width=True):
            query_to_run = "Provide a comprehensive executive summary of this synthetic cohort's academic health and risk profile."
    with pcol6:
        if st.button("🚨 Explain High-Risk Roster", use_container_width=True):
            query_to_run = "Explain the distribution of high-risk students and recommend prioritized triage actions for school counselors."

    custom_query = st.text_area(
        "Or type a custom research or district policy question:",
        value=query_to_run if query_to_run else "",
        placeholder="e.g. How does assignment completion rate correlate with student risk in mathematics courses?",
        height=90,
    )

    if st.button("⚡ Generate AI Insight via Groq", type="primary", use_container_width=True):
        active_query = custom_query.strip() if custom_query.strip() else "Provide a comprehensive pedagogical summary and risk diagnosis of this cohort."
        with st.spinner("Querying Groq LPU Inference Engine..."):
            result = GroqInsightsEngine.generate_insight(
                df=students_df,
                user_query=active_query,
                api_key=st.session_state.get("groq_api_key", ""),
                model=model_choice,
            )

            st.markdown("---")
            if result.get("success"):
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span class="pill pill-emerald">✓ GROQ INFERENCE COMPLETE</span>
                        <span style="font-size: 0.75rem; color: #94a3b8; font-family: 'JetBrains Mono';">Model: {result.get('model_used')} • Tokens: {result.get('tokens_used', 'N/A')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(f"<div class='glass-container'>{result['response']}</div>", unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ {result.get('message')}")
                if "fallback" in result:
                    st.markdown("##### 📊 Automated Heuristic Summary (Offline Fallback Mode):")
                    st.markdown(f"<div class='glass-container'>{result['fallback']}</div>", unsafe_allow_html=True)


def render_simulator_view(students_df: pd.DataFrame):
    """Page 6: Scenario Simulator."""
    st.markdown("### 🔮 What-If Policy & Intervention Simulator")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Model hypothetical district policy changes and evaluate projected shifts in cohort engagement and risk tiers.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="glass-container" style="border-left: 4px solid #3b82f6;">
            <b>ℹ️ Simulation Notice</b>: This module models hypothetical shifts in student behavior. Projections are intended for scenario planning and do not claim causal predictive certainty.
        </div>
        """,
        unsafe_allow_html=True,
    )

    scol1, scol2 = st.columns(2)
    with scol1:
        att_delta = st.slider("Hypothetical Shift in Attendance (%)", min_value=-30.0, max_value=30.0, value=10.0, step=1.0)
        part_delta = st.slider("Hypothetical Shift in Classroom Participation (%)", min_value=-30.0, max_value=30.0, value=15.0, step=1.0)
    with scol2:
        assign_delta = st.slider("Hypothetical Shift in Assignment Completion (%)", min_value=-30.0, max_value=30.0, value=12.0, step=1.0)
        lms_delta = st.slider("Hypothetical Shift in LMS Digital Activity (%)", min_value=-50.0, max_value=50.0, value=20.0, step=5.0)

    sim_df, sim_summary = ScenarioSimulator.run_simulation(
        base_df=students_df,
        att_delta=att_delta,
        part_delta=part_delta,
        assign_delta=assign_delta,
        lms_delta=lms_delta,
    )

    st.markdown("#### 🎯 Projected Impact of Intervention Policy")
    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    with bcol1:
        att_change = sim_summary['sim_avg_attendance'] - sim_summary['baseline_avg_attendance']
        st.markdown(render_kpi("Simulated Attendance", f"{sim_summary['sim_avg_attendance']}%", f"{'+' if att_change>=0 else ''}{att_change:.1f}% vs Baseline", "Projected", "emerald"), unsafe_allow_html=True)
    with bcol2:
        eng_change = sim_summary['sim_avg_engagement'] - sim_summary['baseline_avg_engagement']
        st.markdown(render_kpi("Simulated Engagement", f"{sim_summary['sim_avg_engagement']}", f"{'+' if eng_change>=0 else ''}{eng_change:.1f} pts vs Baseline", "Projected", "cyan"), unsafe_allow_html=True)
    with bcol3:
        st.markdown(render_kpi("High-Risk Learners", f"{sim_summary['sim_high_risk_count']}", f"Down from {sim_summary['baseline_high_risk_count']}", "Triage", "amber"), unsafe_allow_html=True)
    with bcol4:
        st.markdown(render_kpi("Students Rescued", f"{sim_summary['students_saved_from_high_risk']}", f"{sim_summary['relative_risk_reduction_pct']}% Relative Risk Drop", "Saved", "emerald"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    base_kpis = DatasetAnalytics.compute_summary_kpis(students_df)
    st.plotly_chart(viz.plot_scenario_comparison(base_kpis, sim_summary), use_container_width=True)


def render_ml_lab_view(students_df: pd.DataFrame):
    """Page 7: Machine Learning Lab."""
    st.markdown("### 🧠 Academic Early-Warning Machine Learning Lab")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Train and evaluate Scikit-learn predictive classifiers on synthetic academic telemetry features.</p>",
        unsafe_allow_html=True,
    )

    ml_col1, ml_col2 = st.columns([1, 1.5])
    with ml_col1:
        st.markdown("##### 🛠️ Model Hyperparameters")
        model_choice = st.selectbox("Classifier Algorithm", options=["Random Forest", "Decision Tree"])
        test_split = st.slider("Testing Dataset Proportion", min_value=0.15, max_value=0.35, value=0.25, step=0.05)
        ml_seed = st.number_input("ML Random Seed", min_value=1, max_value=99999, value=42)
        train_btn = st.button("🚀 Train & Benchmark Classifier", type="primary", use_container_width=True)

    with ml_col2:
        st.markdown(
            """
            <div class="glass-container">
                <h5 style="margin-top: 0; color: #38bdf8;">🔬 Scientific Validation Protocol</h5>
                <p style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 0.4rem;">
                    <b>Target Label:</b> Binary classification of High-Risk Student Status (1 = High Risk, 0 = Non-High).<br>
                    <b>Input Features:</b> Attendance %, In-Class Participation, Assignment Completion %, LMS Weekly Logins, Average Marks, Late Submissions.<br>
                    <b>Data Separation:</b> Stratified train/test split ensuring fair class representation.
                </p>
                <span class="pill pill-amber">Controlled Academic Experiment</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    ml_results = AcademicMLBenchmarker.train_and_evaluate(
        df=students_df,
        model_type=model_choice,
        test_size=test_split,
        random_state=ml_seed,
    )

    if "error" in ml_results:
        st.warning(ml_results["error"])
    else:
        st.markdown("---")
        st.markdown("#### 📈 Benchmark Performance Results")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(render_kpi("Accuracy", f"{(ml_results['accuracy']*100):.1f}%", f"{ml_results['test_samples']} Test Samples", "Accuracy", "blue"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_kpi("Precision", f"{ml_results['precision']:.3f}", "Positive Predictive Value", "Precision", "cyan"), unsafe_allow_html=True)
        with m3:
            st.markdown(render_kpi("Recall", f"{ml_results['recall']:.3f}", "Sensitivity / Coverage", "Recall", "emerald"), unsafe_allow_html=True)
        with m4:
            st.markdown(render_kpi("F1 Score", f"{ml_results['f1_score']:.3f}", "Harmonic Mean", "F1", "emerald"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            st.plotly_chart(viz.plot_confusion_matrix(ml_results["confusion_matrix"]), use_container_width=True)
        with vcol2:
            st.plotly_chart(viz.plot_feature_importances(ml_results["feature_importances"]), use_container_width=True)

        st.info(f"💡 {ml_results['disclaimer']}")


def render_export_view(students_df: pd.DataFrame, weekly_df: pd.DataFrame):
    """Page 8: Data Export Center."""
    st.markdown("### 📥 Dataset Export & Download Center")
    st.markdown(
        "<p style='color: #94a3b8; margin-top: -0.5rem;'>Download currently generated synthetic student data in standard formats for external research and model training.</p>",
        unsafe_allow_html=True,
    )

    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.markdown("##### 📄 Flat Student Cohort Data")
        st.markdown("<p style='font-size: 0.8rem; color: #94a3b8;'>Summary student indicators including attendance, engagement scores, risk levels, and marks.</p>", unsafe_allow_html=True)

        csv_data = students_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Students CSV (Flat Table)",
            data=csv_data,
            file_name="attendsynth_students.csv",
            mime="text/csv",
            use_container_width=True,
        )

        json_data = students_df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button(
            label="⬇️ Download Students JSON",
            data=json_data,
            file_name="attendsynth_students.json",
            mime="application/json",
            use_container_width=True,
        )

    with dcol2:
        st.markdown("##### 📊 Multi-Sheet Excel Workbook")
        st.markdown("<p style='font-size: 0.8rem; color: #94a3b8;'>Includes formatted sheets: Students Cohort, Weekly Longitudinal Time-Series, and Course Analytics.</p>", unsafe_allow_html=True)

        import io
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            students_df.to_excel(writer, sheet_name="Students_Summary", index=False)
            weekly_df.to_excel(writer, sheet_name="Longitudinal_Weekly", index=False)
            DatasetAnalytics.get_course_breakdown(students_df).to_excel(writer, sheet_name="Course_Analytics", index=False)

        excel_data = excel_buffer.getvalue()
        st.download_button(
            label="⬇️ Download Excel Workbook (.xlsx)",
            data=excel_data,
            file_name="attendsynth_complete_dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        weekly_csv = weekly_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Weekly Time-Series CSV",
            data=weekly_csv,
            file_name="attendsynth_weekly_timeseries.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("#### 📋 Live Data Preview")
    st.dataframe(students_df.head(25), use_container_width=True, hide_index=True)
