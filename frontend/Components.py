"""
components.py — small reusable UI pieces, themed via theme.py.

These return HTML snippets meant to be passed to st.markdown(...,
unsafe_allow_html=True), or render directly via st.* calls. Keeping
them here means every "eyebrow label" or "status pill" in the app
looks identical and only needs to change in one place.
"""

import streamlit as st
from Theme import COLORS, FONT_DISPLAY, FONT_BODY, FONT_MONO, bucket_of

def brand_logo():
    """Renders the ByteSolve brand mark: a small tiled-square icon +
    wordmark. Colors read from the live COLORS dict so it stays legible
    on every palette, including Midnight."""
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
            <svg width="38" height="38" viewBox="0 0 26 26" xmlns="http://www.w3.org/2000/svg">
                <rect x="1" y="1" width="24" height="24" rx="7" fill="{COLORS['ballpoint']}"/>
                <rect x="6" y="6" width="6" height="6" rx="1.5" fill="{COLORS['card']}"/>
                <rect x="14" y="6" width="6" height="6" rx="1.5" fill="{COLORS['card']}" opacity="0.55"/>
                <rect x="6" y="14" width="6" height="6" rx="1.5" fill="{COLORS['card']}" opacity="0.55"/>
                <rect x="14" y="14" width="6" height="6" rx="1.5" fill="{COLORS['card']}"/>
            </svg>
            <span style='font-family:{FONT_DISPLAY}; font-size:23px; font-weight:700; "
            f"letter-spacing:-0.01em; color:{COLORS['ink']};'>Byte<span style='color:{COLORS['ballpoint']};'>Solve</span></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def eyebrow(text: str):
    """Small uppercase mono label used at the top of a card/section."""
    st.markdown(
        f"<div style='font-family:{FONT_MONO}; font-size:11px; letter-spacing:0.1em; "
        f"text-transform:uppercase; color:{COLORS['ballpoint']}; margin-bottom:10px; "
        f"font-weight:500;'>{text}</div>",
        unsafe_allow_html=True,
    )


def highlight_span(text: str, color: str = None) -> str:
    """Returns an inline HTML span styled like a highlighter stroke, tuned
    per-palette (color defaults to COLORS['highlight_bg']) so the ink-
    colored text sitting on top always stays readable — bright stripes on
    light palettes, a dark warm stripe on Midnight.
    Use inside an f-string passed to st.markdown(..., unsafe_allow_html=True)."""
    color = color or COLORS["highlight_bg"]
    return (
        f"<span style='background: linear-gradient(180deg, transparent 58%, "
        f"{color} 58%, {color} 88%, transparent 88%); padding: 0 2px;'>{text}</span>"
    )


def status_pill(mastery: float):
    """Renders a small colored pill showing mastery status."""
    label, color = bucket_of(mastery)
    st.markdown(
        f"<span style='display:inline-flex; align-items:center; gap:6px; "
        f"font-family:{FONT_MONO}; font-size:11px; color:{color}; "
        f"border:1px solid {color}55; background:{color}14; border-radius:20px; "
        f"padding:3px 10px; font-weight:500;'>"
        f"<span style='width:6px; height:6px; border-radius:50%; background:{color};'></span>"
        f"{label}</span>",
        unsafe_allow_html=True,
    )


def progress_bar(value: float, color: str):
    """Renders a slim colored progress bar (0..1). Width animates smoothly
    so score updates (e.g. after a quiz) feel snappy rather than jumping."""
    value = max(0.0, min(1.0, value))
    st.markdown(
        f"<div style='height:6px; background:{COLORS['paper_line']}; border-radius:4px; "
        f"overflow:hidden;'><div style='width:{value*100:.1f}%; height:100%; "
        f"background:{color}; transition:width 450ms ease;'></div></div>",
        unsafe_allow_html=True,
    )


def section_title(text: str):
    st.markdown(
        f"<h1 style='font-family:{FONT_DISPLAY}; font-size:28px; font-weight:700; "
        f"margin:0 0 4px 0;'>{text}</h1>",
        unsafe_allow_html=True,
    )


def chapter_dot_label(name: str, color: str, suffix: str = "", prefix: str = ""):
    """Small colored dot + chapter name. Used to visually tie a chapter to
    its color elsewhere in the app (e.g. its pie-chart slice), the same way
    the Chapters tab's breakdown already does. `prefix` renders before the
    name (e.g. a weight %), `suffix` renders after."""
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:8px; margin-bottom:2px;'>"
        f"<span style='width:9px; height:9px; border-radius:50%; background:{color}; "
        f"flex-shrink:0;'></span>"
        f"<span style='font-family:{FONT_BODY}; font-size:13.5px; font-weight:500;'>"
        f"{prefix}{name}{suffix}</span></div>",
        unsafe_allow_html=True,
    )


def eyebrow_page_label(text: str):
    st.markdown(
        f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ballpoint']}; "
        f"letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;'>{text}</div>",
        unsafe_allow_html=True,
    )


def stat_chip_row(counts: dict):
    """Renders a row of three compact chips summarizing chapter counts by
    status bucket: {"Solid": n, "Practicing": n, "Needs work": n}. Built
    for the trimmed-down Overview tab — a glance-able summary that doesn't
    require reading a full chapter-by-chapter list (that lives in the
    Chapters tab)."""
    bucket_colors = {
        "Solid": COLORS["mint"],
        "Practicing": COLORS["amber"],
        "Needs work": COLORS["coral"],
    }
    chips = "".join(
        f"<div style='flex:1; text-align:center; padding:12px 8px; border-radius:12px; "
        f"background:{bucket_colors[label]}14; border:1px solid {bucket_colors[label]}33;'>"
        f"<div style='font-family:{FONT_DISPLAY}; font-size:24px; font-weight:700; "
        f"color:{bucket_colors[label]};'>{counts.get(label, 0)}</div>"
        f"<div style='font-family:{FONT_MONO}; font-size:10.5px; text-transform:uppercase; "
        f"letter-spacing:0.06em; color:{COLORS['ink_muted']}; margin-top:2px;'>{label}</div>"
        f"</div>"
        for label in ("Solid", "Practicing", "Needs work")
    )
    st.markdown(
        f"<div style='display:flex; gap:10px;'>{chips}</div>",
        unsafe_allow_html=True,
    )
