"""
app.py — entry point. Run with:

    python -m streamlit run app.py

This file only handles page setup, session state, and tab routing.
Design lives in theme.py, content lives in data.py, and each tab's
logic lives in tabs.py — that's where almost all future changes
should happen, not here.
"""

import streamlit as st

from Theme import inject_global_css, COLORS, FONT_MONO
from Data import get_default_chapters
from Tabs import overview_tab, weighting_tab, checkin_tab, plan_tab

st.set_page_config(page_title="Study Planner", page_icon="📓", layout="wide")
inject_global_css()

# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
if "chapters" not in st.session_state:
    st.session_state.chapters = get_default_chapters()


def reset_all():
    st.session_state.chapters = get_default_chapters()
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
with st.container():
    col_title, col_reset = st.columns([5, 1])
    with col_title:
        st.markdown(
            f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ballpoint']}; "
            f"letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;'>"
            f"Study Planner · Prototype</div>",
            unsafe_allow_html=True,
        )
        st.title("Where should you study next?")
    with col_reset:
        st.write("")
        st.write("")
        if st.button("↺ Reset"):
            reset_all()
            st.rerun()

# ---------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------
tab_overview, tab_weighting, tab_checkin, tab_plan = st.tabs(
    ["Overview", "Weighting", "Check-in", "Plan"]
)

with tab_overview:
    overview_tab(st.session_state.chapters)

with tab_weighting:
    weighting_tab(st.session_state.chapters)

with tab_checkin:
    checkin_tab(st.session_state.chapters)

with tab_plan:
    plan_tab(st.session_state.chapters)