"""
theme.py — all visual design tokens live here.

Design lives entirely in PALETTES below. Nothing else in the project
should hardcode a color or font — always read from COLORS /
CHAPTER_HUES, which this module keeps updated in place.

How the live palette-switching works
-------------------------------------
COLORS and CHAPTER_HUES are module-level MUTABLE containers (a dict
and a list), not values. Other files do `from Theme import COLORS`
once at import time — that binds a *reference* to the same dict
object. `set_palette()` never reassigns COLORS to a new dict; it
clears and re-fills the existing one (`COLORS.clear(); COLORS.update(...)`).
Every other module that already imported COLORS sees the change
immediately on the next read, with no re-import or refactor needed.
Call `set_palette(name)` once near the top of app.py, before
`inject_global_css()`, on every rerun (Streamlit reruns the whole
script on each interaction, so this naturally stays in sync with
whatever the sidebar has selected).
"""

import streamlit as st

# ---------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------
# Each palette is self-contained and tuned so text colors ("ink",
# "ink_muted", and the status colors "mint"/"amber"/"coral" used as
# TEXT) hold at least WCAG AA contrast (~4.5:1) against both "paper"
# and "card". CHAPTER_HUES / "yellow_hi" are decorative (bars, dots,
# low-opacity fills) and don't carry text, so they can run brighter.
#
# highlight_bg is the solid stripe drawn *behind* headline text by
# highlight_span() — tuned per palette so the ink color sitting on
# top of it always stays readable (this is why Midnight uses a dark
# gold stripe instead of a bright one: its ink is light).
PALETTES = {
    "Study Desk": {
        "description": "Warm paper & ink, highlighter accents",
        "colors": {
            "paper": "#FAF7EF",
            "paper_line": "#E6E0CE",
            "card": "#FFFFFF",
            "ink": "#20201B",
            "ink_muted": "#6B6554",
            "ballpoint": "#2C4FCF",
            "ballpoint_dim": "#5D74D9",
            "mint": "#1F7A4D",
            "amber": "#A8650E",
            "coral": "#C1432E",
            "yellow_hi": "#FFE066",
            "pink_hi": "#FF9FB8",
            "highlight_bg": "#FFE066",
        },
        "hues": ["#2C4FCF", "#A8650E", "#1F7A4D", "#C1432E", "#6F53C4", "#0C7A86", "#9C3E76", "#4C7A2E"],
    },
    "Slate Minimal": {
        "description": "Cool neutral gray, indigo accent — modern SaaS",
        "colors": {
            "paper": "#F3F4F7",
            "paper_line": "#E1E3E8",
            "card": "#FFFFFF",
            "ink": "#14161B",
            "ink_muted": "#565C68",
            "ballpoint": "#4338CA",
            "ballpoint_dim": "#6366F1",
            "mint": "#15803D",
            "amber": "#B45309",
            "coral": "#B91C1C",
            "yellow_hi": "#FDE68A",
            "pink_hi": "#FBCFE8",
            "highlight_bg": "#FDE68A",
        },
        "hues": ["#4338CA", "#B45309", "#15803D", "#B91C1C", "#7C3AED", "#0F766E", "#BE185D", "#4D7C0F"],
    },
    "Midnight": {
        "description": "Dark mode — soft blue glow on near-black",
        "colors": {
            "paper": "#101218",
            "paper_line": "#262A35",
            "card": "#181B23",
            "ink": "#EEF0F4",
            "ink_muted": "#A0A6B4",
            "ballpoint": "#7DA6FF",
            "ballpoint_dim": "#5B82D8",
            "mint": "#5FE39B",
            "amber": "#FFC24B",
            "coral": "#FF8A80",
            "yellow_hi": "#FFD166",
            "pink_hi": "#FF9FB8",
            "highlight_bg": "#3A3315",
        },
        "hues": ["#7DA6FF", "#FFC24B", "#5FE39B", "#FF8A80", "#B7A2FF", "#63D9E0", "#FF8FC7", "#B7DD6B"],
    },
    "Sage & Clay": {
        "description": "Earthy sage & terracotta, soft and calm",
        "colors": {
            "paper": "#F2EFE6",
            "paper_line": "#E1DBC8",
            "card": "#FFFFFF",
            "ink": "#2A2721",
            "ink_muted": "#6B6656",
            "ballpoint": "#A9502F",
            "ballpoint_dim": "#C36F4C",
            "mint": "#3F6B45",
            "amber": "#96691C",
            "coral": "#A23B33",
            "yellow_hi": "#E8C468",
            "pink_hi": "#D8A0A0",
            "highlight_bg": "#F0D28A",
        },
        "hues": ["#A9502F", "#96691C", "#3F6B45", "#A23B33", "#6B5B95", "#3E6E6E", "#8A4E73", "#7C8A3E"],
    },
    "Nordic Frost": {
        "description": "Cool blue-gray, crisp and quiet",
        "colors": {
            "paper": "#ECEFF4",
            "paper_line": "#D8DEE9",
            "card": "#FFFFFF",
            "ink": "#2E3440",
            "ink_muted": "#4C566A",
            "ballpoint": "#3B5BA5",
            "ballpoint_dim": "#5E81AC",
            "mint": "#3C7A5B",
            "amber": "#A8790C",
            "coral": "#A8434C",
            "yellow_hi": "#EBCB8B",
            "pink_hi": "#D9A0BF",
            "highlight_bg": "#EBCB8B",
        },
        "hues": ["#3B5BA5", "#A8790C", "#3C7A5B", "#A8434C", "#7A5DA6", "#3C8590", "#9C4E7A", "#6C8B3C"],
    },
    "Sunset Pop": {
        "description": "Cream base, punchy magenta & gold accents",
        "colors": {
            "paper": "#FBF3EC",
            "paper_line": "#F0DECF",
            "card": "#FFFFFF",
            "ink": "#241C1A",
            "ink_muted": "#71615A",
            "ballpoint": "#9D2168",
            "ballpoint_dim": "#C2427E",
            "mint": "#2F7A4F",
            "amber": "#B5670A",
            "coral": "#C23B2E",
            "yellow_hi": "#FFD166",
            "pink_hi": "#FFADC6",
            "highlight_bg": "#FFD166",
        },
        "hues": ["#9D2168", "#B5670A", "#2F7A4F", "#C23B2E", "#6A4C93", "#1D7A85", "#D6604D", "#8C6A3F"],
    },
}

DEFAULT_PALETTE = "Study Desk"

# Mutable containers — see module docstring. Populated by set_palette()
# below; never reassign these names, only .clear()/.update()/.extend().
COLORS: dict = {}
CHAPTER_HUES: list = []


def palette_names() -> list:
    return list(PALETTES.keys())


def set_palette(name: str) -> dict:
    """Activate a palette by name, mutating COLORS/CHAPTER_HUES in place
    so every module that already did `from Theme import COLORS` picks up
    the change on its next read. Returns the active color dict."""
    palette = PALETTES.get(name, PALETTES[DEFAULT_PALETTE])
    COLORS.clear()
    COLORS.update(palette["colors"])
    CHAPTER_HUES.clear()
    CHAPTER_HUES.extend(palette["hues"])
    return COLORS


# Populate with the default immediately so anything imported before
# app.py calls set_palette() (e.g. a bare `import Theme` in a test)
# still gets a usable, non-empty palette.
set_palette(DEFAULT_PALETTE)

FONT_DISPLAY = '"Space Grotesk", "Segoe UI", sans-serif'   # headings
FONT_BODY = '"IBM Plex Sans", "Segoe UI", sans-serif'       # body text
FONT_MONO = '"IBM Plex Mono", "Courier New", monospace'     # data / labels


def bucket_of(mastery: float):
    """Map a 0..1 mastery score to a (label, color) status bucket.
    Reads COLORS at call time, so it always reflects the active palette."""
    if mastery >= 0.7:
        return "Solid", COLORS["mint"]
    if mastery >= 0.4:
        return "Practicing", COLORS["amber"]
    return "Needs work", COLORS["coral"]


def inject_global_css():
    """Call once per page load (after set_palette) to apply the active
    theme to the whole app, including Streamlit's native chrome so
    dark palettes don't leave stray white widgets behind."""
    C = COLORS
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        * {{
            transition: background-color 160ms ease, border-color 160ms ease,
                        color 160ms ease, box-shadow 160ms ease, transform 90ms ease;
        }}

        .stApp {{
            background-color: {C['paper']};
        }}

        html, body, [class*="css"] {{
            font-family: {FONT_BODY};
            color: {C['ink']};
        }}

        h1, h2, h3 {{
            font-family: {FONT_DISPLAY} !important;
            color: {C['ink']} !important;
        }}

        p, span, label, li {{ color: {C['ink']}; }}

        [data-testid="stCaptionContainer"], .stMarkdown small {{
            color: {C['ink_muted']} !important;
        }}

        /* ---- Sidebar ---- */
        [data-testid="stSidebar"] {{
            background-color: {C['card']};
            border-right: 1px solid {C['paper_line']};
        }}
        [data-testid="stSidebar"] * {{ color: {C['ink']}; }}

        /* ---- Buttons ---- */
        .stButton > button {{
            background: {C['ballpoint']};
            color: #ffffff;
            border-radius: 10px;
            border: none;
            font-family: {FONT_DISPLAY};
            font-weight: 600;
            padding: 0.5rem 1.1rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.08);
        }}
        .stButton > button:hover {{
            background: {C['ballpoint_dim']};
            color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 4px 10px -4px rgba(0,0,0,0.35);
        }}
        .stButton > button:active {{ transform: scale(0.97); }}

        /* ---- Bordered containers ("cards") ---- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {C['card']};
            border: 1px solid {C['paper_line']} !important;
            border-radius: 14px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}

        /* ---- Tabs — pill style, snappy ---- */
        button[data-baseweb="tab"] {{
            font-family: {FONT_DISPLAY};
            font-weight: 600;
            font-size: 13.5px;
            color: {C['ink_muted']};
            border-radius: 8px 8px 0 0;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {C['ballpoint']};
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {C['ballpoint']} !important;
            height: 2.5px !important;
        }}
        div[data-baseweb="tab-border"] {{ background-color: {C['paper_line']} !important; }}

        /* ---- Sliders ---- */
        div[data-baseweb="slider"] > div > div > div {{ background: {C['ballpoint']} !important; }}
        div[data-baseweb="slider"] div[role="slider"] {{ background: {C['ballpoint']} !important; }}

        /* ---- Radio buttons (quiz options) ---- */
        div[role="radiogroup"] label {{ font-family: {FONT_MONO}; font-size: 12.5px; }}

        /* ---- Select boxes / number inputs / text inputs ---- */
        div[data-baseweb="select"] > div, .stNumberInput input, .stTextInput input {{
            background-color: {C['card']} !important;
            border-color: {C['paper_line']} !important;
            color: {C['ink']} !important;
            border-radius: 8px;
        }}
        [data-baseweb="popover"] li, [data-baseweb="menu"] {{
            background-color: {C['card']} !important;
            color: {C['ink']} !important;
        }}
        [data-baseweb="popover"] li:hover {{ background-color: {C['paper']} !important; }}

        /* ---- Metrics ---- */
        [data-testid="stMetricValue"] {{ color: {C['ink']}; font-family: {FONT_DISPLAY}; }}
        [data-testid="stMetricLabel"] {{ color: {C['ink_muted']}; }}

        /* ---- Divider ---- */
        hr {{ border-color: {C['paper_line']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
