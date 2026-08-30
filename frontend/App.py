import requests
import streamlit as st

import Theme
from Theme import COLORS, FONT_MONO, DEFAULT_PALETTE, PALETTES
from Tabs import home_tab, overview_tab, chapters_tab, weighting_tab, checkin_tab, plan_tab
from Components import brand_logo
from api_client import get_or_create_student, fetch_chapters, API_BASE

st.set_page_config(page_title="Study Planner", page_icon="📓", layout="wide")

if "palette" not in st.session_state:
    st.session_state.palette = DEFAULT_PALETTE
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

Theme.set_palette(st.session_state.palette)
Theme.inject_global_css()

# Nav-button styling: make st.sidebar buttons look like a menu list
# rather than default full-width Streamlit buttons.
st.markdown(
    f"""
    <style>
    section[data-testid="stSidebar"] button {{
        justify-content: flex-start !important;
        text-align: left !important;
        font-family: {FONT_MONO};
        font-size: 13px;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }}
    section[data-testid="stSidebar"] button:hover {{
        color: {COLORS['ballpoint']} !important;
    }}
    section[data-testid="stSidebar"] button[kind="primary"] {{
        background: {COLORS['yellow_hi']}30 !important;
        color: {COLORS['ink']} !important;
        font-weight: 600;
    }}

    /* Swap the native sidebar collapse/expand control's icon for a
       hamburger (three lines) — same button, same click behavior,
       just a different glyph drawn on top of it. */
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stExpandSidebarButton"] svg,
    [data-testid="collapsedControl"] svg,
    [data-testid="baseButton-headerNoPadding"] svg {{
        display: none !important;
    }}
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"] button,
    [data-testid="collapsedControl"] button {{
        position: relative;
    }}
    [data-testid="stSidebarCollapseButton"] button::after,
    [data-testid="stExpandSidebarButton"] button::after,
    [data-testid="collapsedControl"] button::after {{
        content: "";
        display: block;
        width: 20px;
        height: 14px;
        background-image: repeating-linear-gradient(
            {COLORS['ink']} 0px, {COLORS['ink']} 2px, transparent 2px, transparent 6px
        );
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


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


# ---------------------------------------------------------------------
# LEFT — navigation sidebar. Streamlit's native collapse arrow at the
# top of the page already acts as the "menu button" that opens/closes
# this panel.
# ---------------------------------------------------------------------
NAV_ITEMS = ["Home", "Overview", "Chapters", "Weighting", "Practice", "Plan"]

with st.sidebar:
    brand_logo()
    st.markdown(
        f"<div style='font-family:{FONT_MONO}; font-size:10.5px; color:{COLORS['ink_muted']}; "
        f"letter-spacing:0.1em; text-transform:uppercase; margin:2px 0 14px;'>Menu</div>",
        unsafe_allow_html=True,
    )
    for item in NAV_ITEMS:
        is_current = st.session_state.nav_page == item
        if st.button(
            item,
            key=f"nav_{item}",
            use_container_width=True,
            type="primary" if is_current else "secondary",
        ):
            st.session_state.nav_page = item
            st.rerun()

# ---------------------------------------------------------------------
# TOP — title on the left, settings popover (theme picker) on the right
# ---------------------------------------------------------------------
header_l, header_r = st.columns([10, 1])

with header_l:
    st.markdown(
        f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ballpoint']}; "
        f"letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;'>"
        f"Study Planner · Prototype</div>",
        unsafe_allow_html=True,
    )
    st.title(st.session_state.nav_page if st.session_state.nav_page != "Home" else "Where should you study next?")

with header_r:
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    with st.popover("⚙️", use_container_width=True):
        st.markdown(
            f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ballpoint']}; "
            f"letter-spacing:0.1em; text-transform:uppercase; margin-bottom:2px;'>Settings</div>",
            unsafe_allow_html=True,
        )
        st.markdown("**Appearance**")
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
        st.markdown("**Data**")
        st.caption(f"Backend: `{API_BASE}`")
        st.caption(f"Student id: `{st.session_state.get('student_id', '—')}`")
        if st.button("↺ Reset all progress", use_container_width=True):
            reset_all()
            st.rerun()

# ---------------------------------------------------------------------
# PAGE CONTENT
# ---------------------------------------------------------------------
page = st.session_state.nav_page
if page == "Home":
    home_tab(st.session_state.chapters)
elif page == "Overview":
    overview_tab(st.session_state.chapters)
elif page == "Chapters":
    chapters_tab(st.session_state.chapters)
elif page == "Weighting":
    weighting_tab(st.session_state.chapters)
elif page == "Practice":
    checkin_tab(st.session_state.chapters)
elif page == "Plan":
    plan_tab(st.session_state.chapters)
