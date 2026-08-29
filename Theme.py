"""
theme.py — all visual design tokens live here.

To restyle the whole app, change values in COLORS / FONT_* below.
Nothing else in the project should hardcode a color or font name —
always import from here so a single edit propagates everywhere.
"""

import streamlit as st

# ---------------------------------------------------------------------
# Palette — "study desk": warm paper, ink-black text, highlighter accents
# ---------------------------------------------------------------------
COLORS = {
    "paper": "#FAF7EF",       # app background
    "paper_line": "#E6E0CE",  # borders, dividers, dot-grid
    "card": "#FFFFFF",        # card / panel background
    "ink": "#20201B",         # primary text
    "ink_muted": "#7A7460",   # secondary text
    "ballpoint": "#2C4FCF",   # primary action color (buttons, links)
    "ballpoint_dim": "#5D74D9",
    "mint": "#2F9E68",        # "mastered / good" status
    "amber": "#C87F17",       # "practicing / okay" status
    "coral": "#D65A45",       # "needs work" status
    "yellow_hi": "#FFE066",   # highlighter yellow (emphasis)
    "pink_hi": "#FF9FB8",     # highlighter pink (secondary emphasis)
}

# Rotating palette used for per-chapter chart colors / dots
CHAPTER_HUES = [
    "#2C4FCF", "#C87F17", "#2F9E68", "#D65A45",
    "#7A5FD6", "#0F9AA8", "#B34A8C", "#5C8A3A",
]

FONT_DISPLAY = '"Space Grotesk", "Segoe UI", sans-serif'   # headings
FONT_BODY = '"IBM Plex Sans", "Segoe UI", sans-serif'       # body text
FONT_MONO = '"IBM Plex Mono", "Courier New", monospace'     # data / labels


def bucket_of(mastery: float):
    """Map a 0..1 mastery score to a (label, color) status bucket."""
    if mastery >= 0.7:
        return "Solid", COLORS["mint"]
    if mastery >= 0.4:
        return "Practicing", COLORS["amber"]
    return "Needs work", COLORS["coral"]


def inject_global_css():
    """Call once per page load to apply the theme to the whole app."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        .stApp {{
            background-color: {COLORS['paper']};
            background-image: radial-gradient({COLORS['paper_line']} 1px, transparent 1px);
            background-size: 22px 22px;
        }}

        html, body, [class*="css"] {{
            font-family: {FONT_BODY};
            color: {COLORS['ink']};
        }}

        h1, h2, h3 {{
            font-family: {FONT_DISPLAY} !important;
            color: {COLORS['ink']} !important;
        }}

        /* Buttons */
        .stButton > button {{
            background: {COLORS['ballpoint']};
            color: #ffffff;
            border-radius: 10px;
            border: none;
            font-family: {FONT_DISPLAY};
            font-weight: 600;
            padding: 0.5rem 1.1rem;
        }}
        .stButton > button:hover {{
            background: {COLORS['ballpoint_dim']};
            color: #ffffff;
        }}

        /* Bordered containers (our "cards") */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {COLORS['card']};
            border: 1px solid {COLORS['paper_line']} !important;
            border-radius: 14px !important;
            box-shadow: 0 1px 2px rgba(32,32,27,0.04), 0 8px 20px -12px rgba(32,32,27,0.15);
        }}

        /* Tabs styled like index-card tabs */
        button[data-baseweb="tab"] {{
            font-family: {FONT_DISPLAY};
            font-weight: 600;
            font-size: 14px;
        }}

        /* Slider accent color */
        div[data-baseweb="slider"] > div > div > div {{
            background: {COLORS['ballpoint']} !important;
        }}

        /* Radio buttons used for quiz options */
        div[role="radiogroup"] label {{
            font-family: {FONT_MONO};
            font-size: 12.5px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
