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
    fresh_chapters = get_default_chapters()
    st.session_state.chapters = fresh_chapters
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False

    # Sliders/radios keep their OWN value in session_state once you've
    # touched them, and Streamlit ignores value= on later reruns as long
    # as that key still exists -- so resetting st.session_state.chapters
    # alone doesn't move the widgets, and weighting_tab's very next
    # `c["weight_pct"] = new_w` would silently write the stale slider
    # value straight back into the fresh data. Clearing the widgets'
    # own keys makes Streamlit treat them as new next render, so they
    # actually pick up the fresh value= again.
    for c in fresh_chapters:
        st.session_state.pop(f"weight_{c['id']}", None)

    # Question radios are keyed by question id (q001, q002, ...), not by
    # chapter id, and there can be dozens of them -- sweep every quiz_*
    # key rather than trying to enumerate them.
    for key in [k for k in st.session_state.keys() if k.startswith("quiz_")]:
        st.session_state.pop(key, None)

    # The topic selector in Check-in has the same sticky-key behavior as
    # the sliders above -- clear it so Reset also puts the user back on
    # the first chapter instead of leaving them on whatever they'd picked.
    st.session_state.pop("checkin_chapter_select", None)
    st.session_state.checkin_chapter_id = fresh_chapters[0]["id"]


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