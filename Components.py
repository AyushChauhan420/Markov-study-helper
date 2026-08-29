"""
components.py — small reusable UI pieces, themed via theme.py.

These return HTML snippets meant to be passed to st.markdown(...,
unsafe_allow_html=True), or render directly via st.* calls. Keeping
them here means every "eyebrow label" or "status pill" in the app
looks identical and only needs to change in one place.
"""

import streamlit as st
from Theme import COLORS, FONT_DISPLAY, FONT_BODY, FONT_MONO, bucket_of


def eyebrow(text: str):
    """Small uppercase mono label used at the top of a card/section."""
    st.markdown(
        f"<div style='font-family:{FONT_MONO}; font-size:11px; letter-spacing:0.1em; "
        f"text-transform:uppercase; color:{COLORS['ballpoint']}; margin-bottom:10px; "
        f"font-weight:500;'>{text}</div>",
        unsafe_allow_html=True,
    )


def highlight_span(text: str, color: str = None) -> str:
    """Returns an inline HTML span styled like a highlighter stroke.
    Use inside an f-string passed to st.markdown(..., unsafe_allow_html=True)."""
    color = color or COLORS["yellow_hi"]
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
    """Renders a slim colored progress bar (0..1)."""
    value = max(0.0, min(1.0, value))
    st.markdown(
        f"<div style='height:6px; background:{COLORS['paper_line']}; border-radius:4px; "
        f"overflow:hidden;'><div style='width:{value*100:.1f}%; height:100%; "
        f"background:{color};'></div></div>",
        unsafe_allow_html=True,
    )


def section_title(text: str):
    st.markdown(
        f"<h1 style='font-family:{FONT_DISPLAY}; font-size:28px; font-weight:700; "
        f"margin:0 0 4px 0;'>{text}</h1>",
        unsafe_allow_html=True,
    )


def chapter_dot_label(name: str, color: str, suffix: str = ""):
    """Small colored dot + chapter name. Used to visually tie a chapter to
    its color elsewhere in the app (e.g. its pie-chart slice), the same way
    the Overview tab's chapter breakdown already does."""
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:8px; margin-bottom:2px;'>"
        f"<span style='width:9px; height:9px; border-radius:50%; background:{color}; "
        f"flex-shrink:0;'></span>"
        f"<span style='font-family:{FONT_BODY}; font-size:13.5px; font-weight:500;'>"
        f"{name}{suffix}</span></div>",
        unsafe_allow_html=True,
    )


def eyebrow_page_label(text: str):
    st.markdown(
        f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ballpoint']}; "
        f"letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;'>{text}</div>",
        unsafe_allow_html=True,
    )
