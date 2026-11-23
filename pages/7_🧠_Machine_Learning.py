import streamlit as st
from styles.theme import apply_theme, render_brand_header
from core.views import render_ml_lab_view
from core.data_generator import SyntheticDataGenerator, DEFAULT_COURSES

st.set_page_config(page_title="Machine Learning - AttendSynth AI", page_icon="🧠", layout="wide")
apply_theme()

if "students_df" not in st.session_state or st.session_state["students_df"] is None:
    gen = SyntheticDataGenerator(seed=42)
    s_df, w_df = gen.generate_cohort(num_students=250, num_weeks=16, courses=DEFAULT_COURSES)
    st.session_state["students_df"] = s_df
    st.session_state["weekly_df"] = w_df

render_brand_header()
render_ml_lab_view(st.session_state["students_df"])
