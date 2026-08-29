import requests
import streamlit as st

import Theme
from Theme import COLORS, FONT_MONO, DEFAULT_PALETTE, PALETTES
from Tabs import overview_tab, chapters_tab, weighting_tab, checkin_tab, plan_tab
from Components import brand_logo
from api_client import get_or_create_student, fetch_chapters, API_BASE

st.set_page_config(page_title="Study Planner", page_icon="📓", layout="wide")

if "palette" not in st.session_state:
    st.session_state.palette = DEFAULT_PALETTE
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

Theme.set_palette(st.session_state.palette)
Theme.inject_global_css()


def load_chapters():
    student_id = get_or_create_student()
    st.session_state.chapters = fetch_chapters(student_id)


try:
    if "chapters" not in st.session_state:
        load_chapters()
except requests.exceptions.ConnectionError:
    st.error(
        f"Can't reach the Study Planner API at `{API_BASE}`. "
        "Start the backend first: `cd backend && uvicorn main:app --reload`."
    )
    st.stop()


def reset_all():
    for c in st.session_state.chapters:
        st.session_state.pop(f"weight_{c['id']}", None)
    for key in [k for k in st.session_state.keys() if k.startswith("quiz_")]:
        st.session_state.pop(key, None)
    st.session_state.pop("checkin_chapter_select", None)
    st.session_state.pop("student_id", None)  # fresh guest -> fresh mastery
    load_chapters()
    st.session_state.checkin_chapter_id = st.session_state.chapters[0]["id"]


def apply_palette_choice():
    st.session_state.palette = st.session_state.palette_select


header_l, header_r = st.columns([10, 1])

with header_l:
    brand_logo()
    st.markdown(
        f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ballpoint']}; "
        f"letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;'>"
        f"Study Planner · Prototype</div>",
        unsafe_allow_html=True,
    )
    st.title("Where should you study next?")

with header_r:
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    if st.button("☰", key="settings_toggle", help="Settings", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings

if st.session_state.show_settings:
    with st.container(border=True):
        st.markdown(
            f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ballpoint']}; "
            f"letter-spacing:0.1em; text-transform:uppercase; margin-bottom:2px;'>Settings</div>",
            unsafe_allow_html=True,
        )
        st.markdown("### Appearance")

        st.selectbox(
            "Color palette",
            options=list(PALETTES.keys()),
            index=list(PALETTES.keys()).index(st.session_state.palette),
            key="palette_select",
            help="Pick a palette — contrast is checked for readability in every option.",
            on_change=apply_palette_choice,
        )
        st.caption(PALETTES[st.session_state.palette]["description"])

        st.markdown("---")
        st.markdown("### Data")
        st.caption(f"Backend: `{API_BASE}` · student id: `{st.session_state.get('student_id', '—')}`")
        if st.button("↺ Reset all progress", use_container_width=True):
            reset_all()
            st.rerun()

tab_overview, tab_chapters, tab_weighting, tab_checkin, tab_plan = st.tabs(
    ["Overview", "Chapters", "Weighting", "Check-in", "Plan"]
)

with tab_overview:
    overview_tab(st.session_state.chapters)

with tab_chapters:
    chapters_tab(st.session_state.chapters)

with tab_weighting:
    weighting_tab(st.session_state.chapters)

with tab_checkin:
    checkin_tab(st.session_state.chapters)

with tab_plan:
    plan_tab(st.session_state.chapters)
