"""
Dark Navy SaaS Theme and Component Styling for AttendSynth AI.
Provides custom CSS injection and reusable HTML badge/card renderers.
"""

import streamlit as st


DARK_NAVY_CSS = """
<style>
/* =======================================================
   ATTENDSYNTH AI - MODERN DARK NAVY SAAS DASHBOARD THEME
   ======================================================= */

/* Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-primary: #0a0f1d;
    --bg-secondary: #0f172a;
    --bg-card: #131e36;
    --bg-card-hover: #192747;
    --border-color: #1e293b;
    --border-accent: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --color-primary: #3b82f6;
    --color-primary-light: #60a5fa;
    --color-accent: #38bdf8;
    --color-emerald: #10b981;
    --color-amber: #f59e0b;
    --color-rose: #ef4444;
}

/* Global Application Background */
.stApp {
    background: radial-gradient(circle at 15% 15%, #0f1c3f 0%, #0a0f1d 55%, #070a14 100%) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
}

/* Hide default streamlit clutter */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background: transparent !important;}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

p, span, label, div {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

code, .stCode, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #0c1427 !important;
    border-right: 1px solid var(--border-color) !important;
}

section[data-testid="stSidebar"] div.block-container {
    padding-top: 2rem !important;
}

/* Metric / KPI Card Component */
.kpi-card {
    background: linear-gradient(135deg, rgba(19, 30, 54, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(59, 130, 246, 0.15);
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(12px);
    transition: all 0.25s ease-in-out;
    position: relative;
    overflow: hidden;
}

.kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(59, 130, 246, 0.35);
    box-shadow: 0 8px 28px -4px rgba(59, 130, 246, 0.2);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #38bdf8);
    opacity: 0.6;
}

.kpi-title {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-secondary);
    margin-bottom: 0.4rem;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.1;
    margin-bottom: 0.35rem;
}

.kpi-subtitle {
    font-size: 0.75rem;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

/* Custom Status Pills */
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

.pill-emerald {
    background-color: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.28);
}

.pill-amber {
    background-color: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.28);
}

.pill-rose {
    background-color: rgba(239, 68, 68, 0.12);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.28);
}

.pill-blue {
    background-color: rgba(59, 130, 246, 0.12);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.28);
}

/* Glass Section Container */
.glass-container {
    background: rgba(19, 30, 54, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(8px);
    margin-bottom: 1.5rem;
}

/* Banner Card */
.brand-banner {
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.4) 0%, rgba(15, 23, 42, 0.7) 100%);
    border: 1px solid rgba(59, 130, 246, 0.25);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

/* Streamlit Native Overrides */
.stButton>button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 0.55rem 1.25rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* Input Fields */
.stTextInput>div>div>input, .stSelectbox>div>div, .stNumberInput>div>div>input {
    background-color: #0c1427 !important;
    color: #f8fafc !important;
    border-radius: 10px !important;
    border: 1px solid var(--border-color) !important;
}

.stTextInput>div>div>input:focus, .stSelectbox>div>div:focus {
    border-color: var(--color-primary) !important;
    box-shadow: 0 0 0 1px var(--color-primary) !important;
}

/* Streamlit Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(15, 23, 42, 0.6);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
}

.stTabs [data-baseweb="tab"] {
    height: 40px;
    border-radius: 8px;
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.85rem;
    padding: 0 16px;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background-color: #1e293b !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

/* Streamlit Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border-color) !important;
}
</style>
"""


def apply_theme():
    """Injects the Dark Navy SaaS theme into the current Streamlit page."""
    st.markdown(DARK_NAVY_CSS, unsafe_allow_html=True)


def render_brand_header():
    """Renders the top SaaS header banner with status indicators."""
    st.markdown(
        """
        <div class="brand-banner">
            <div>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #3b82f6, #06b6d4); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; font-weight: 800; color: #0a0f1d; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);">
                        🎓
                    </div>
                    <div>
                        <h2 style="margin: 0; font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em;">AttendSynth AI</h2>
                        <span style="font-size: 0.8rem; color: #94a3b8; font-weight: 500;">Synthetic Student Engagement & Early-Warning Generator</span>
                    </div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
                <span class="pill pill-emerald">● ENGINE READY</span>
                <span class="pill pill-blue">FERPA & ZERO-PII SAFE</span>
                <span class="pill pill-amber">GROQ LPU ENABLED</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(title: str, value: str, subtitle: str = "", pill_text: str = "", pill_color: str = "blue"):
    """Returns HTML for a modern SaaS KPI metric card."""
    pill_html = f'<span class="pill pill-{pill_color}">{pill_text}</span>' if pill_text else ""
    return f"""
    <div class="kpi-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div class="kpi-title">{title}</div>
            {pill_html}
        </div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """
