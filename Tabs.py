"""
tabs.py — one function per tab. Each takes the current chapter list
(from st.session_state) and renders its section of the UI. Chart
styling pulls colors from theme.py so charts stay visually consistent
with the rest of the app automatically.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from Theme import COLORS, CHAPTER_HUES, FONT_DISPLAY, FONT_BODY, FONT_MONO, bucket_of
from Components import eyebrow, highlight_span, status_pill, progress_bar
from Data import QUIZ_BANK, SOURCE_LABEL


def _plotly_base_layout(height=280):
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_MONO, color=COLORS["ink_muted"], size=11),
    )


# ---------------------------------------------------------------------
# OVERVIEW TAB
# ---------------------------------------------------------------------
def overview_tab(chapters):
    total_w = sum(c["weight_pct"] for c in chapters) or 1
    readiness = sum((c["weight_pct"] / total_w) * c["mastery"] * 100 for c in chapters)
    focus_chapter = max(chapters, key=lambda c: c["weight_pct"] * (1 - c["mastery"]))

    col1, col2 = st.columns([1.1, 1])

    with col1:
        with st.container(border=True):
            eyebrow("Where you stand")
            st.markdown(
                f"<div style='font-family:{FONT_DISPLAY}; font-size:15px; "
                f"color:{COLORS['ink_muted']}; margin-bottom:6px;'>"
                f"If the exam were today, you'd score around</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-family:{FONT_DISPLAY}; font-size:56px; font-weight:700; "
                f"line-height:1;'>{highlight_span(f'{readiness:.0f}%')}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-family:{FONT_MONO}; font-size:12px; "
                f"color:{COLORS['ink_muted']}; margin-top:10px;'>"
                f"weighted across {len(chapters)} chapters · source: {SOURCE_LABEL}</div>",
                unsafe_allow_html=True,
            )

    with col2:
        with st.container(border=True):
            eyebrow("Biggest opportunity")
            st.markdown(
                f"<div style='font-family:{FONT_DISPLAY}; font-size:20px; font-weight:600; "
                f"margin-bottom:6px;'>{focus_chapter['name']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-family:{FONT_BODY}; font-size:13px; "
                f"color:{COLORS['ink_muted']}; line-height:1.6;'>"
                f"Worth <strong style='color:{COLORS['ink']}'>{focus_chapter['weight_pct']}%</strong> "
                f"of the exam but only "
                f"<strong style='color:{COLORS['ink']}'>{focus_chapter['mastery']*100:.0f}%</strong> "
                f"mastered — highest expected return on study time right now.</div>",
                unsafe_allow_html=True,
            )

    with st.container(border=True):
        eyebrow("Chapter breakdown")
        sorted_chapters = sorted(chapters, key=lambda c: -c["weight_pct"])
        for i, c in enumerate(sorted_chapters):
            row_l, row_r = st.columns([5, 1])
            with row_l:
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'>"
                    f"<span style='font-family:{FONT_BODY}; font-size:13.5px; font-weight:500;'>{c['name']}</span>"
                    f"<span style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ink_muted']};'>"
                    f"{c['weight_pct']}% of exam</span></div>",
                    unsafe_allow_html=True,
                )
                progress_bar(c["mastery"], CHAPTER_HUES[i % len(CHAPTER_HUES)])
            with row_r:
                st.write("")
                status_pill(c["mastery"])


# ---------------------------------------------------------------------
# WEIGHTING TAB
# ---------------------------------------------------------------------
def weighting_tab(chapters):
    total_w = sum(c["weight_pct"] for c in chapters) or 1
    col1, col2 = st.columns([1.1, 1])

    with col1:
        with st.container(border=True):
            eyebrow("Adjust chapter weighting")
            st.markdown(
                f"<div style='font-family:{FONT_BODY}; font-size:12.5px; "
                f"color:{COLORS['ink_muted']}; margin-bottom:16px; line-height:1.6;'>"
                f"Defaults come from the exam blueprint in <code>data.py</code> — drag to "
                f"correct for a syllabus that runs differently at your school.</div>",
                unsafe_allow_html=True,
            )
            for i, c in enumerate(chapters):
                pct = (c["weight_pct"] / total_w) * 100
                new_w = st.slider(
                    f"{c['name']} · {pct:.0f}%",
                    min_value=1.0, max_value=30.0, value=float(c["weight_pct"]), step=0.5,
                    key=f"weight_{c['id']}",
                )
                c["weight_pct"] = new_w

    with col2:
        with st.container(border=True):
            eyebrow("Exam weight distribution")
            fig = go.Figure(go.Pie(
                labels=[c["name"] for c in chapters],
                values=[c["weight_pct"] for c in chapters],
                hole=0.55,
                marker=dict(colors=CHAPTER_HUES[: len(chapters)], line=dict(color=COLORS["card"], width=2)),
                textinfo="none",
            ))
            fig.update_layout(**_plotly_base_layout(300), legend=dict(font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------
# CHECK-IN TAB (diagnostic quiz)
# ---------------------------------------------------------------------
def checkin_tab(chapters):
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    if st.session_state.quiz_submitted:
        if st.button("↺ Retake"):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.rerun()

    for c in chapters:
        quiz = QUIZ_BANK.get(c["id"])
        if not quiz:
            continue
        with st.container(border=True):
            st.markdown(
                f"<div style='font-family:{FONT_DISPLAY}; font-weight:600; font-size:14.5px; "
                f"margin-bottom:10px;'>{c['name']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-family:{FONT_BODY}; font-size:13.5px; margin-bottom:10px;'>"
                f"{quiz['question']}</div>",
                unsafe_allow_html=True,
            )
            selected = st.radio(
                "options", quiz["options"], index=None, key=f"quiz_{c['id']}",
                label_visibility="collapsed", horizontal=True,
                disabled=st.session_state.quiz_submitted,
            )
            if selected is not None:
                st.session_state.quiz_answers[c["id"]] = quiz["options"].index(selected)
            if st.session_state.quiz_submitted:
                correct_opt = quiz["options"][quiz["correct_index"]]
                st.markdown(
                    f"<div style='font-family:{FONT_MONO}; font-size:12px; color:{COLORS['mint']};'>"
                    f"✓ Correct answer: {correct_opt}</div>",
                    unsafe_allow_html=True,
                )

    if not st.session_state.quiz_submitted:
        if st.button("Check my answers →", type="primary"):
            for c in chapters:
                quiz = QUIZ_BANK.get(c["id"])
                if not quiz:
                    continue
                selected_idx = st.session_state.quiz_answers.get(c["id"])
                correct = selected_idx == quiz["correct_index"]
                c["mastery"] = min(0.95, c["mastery"] + 0.25) if correct else max(0.08, c["mastery"] - 0.10)
            st.session_state.quiz_submitted = True
            st.rerun()


# ---------------------------------------------------------------------
# PLAN TAB
# ---------------------------------------------------------------------
def plan_tab(chapters):
    with st.container(border=True):
        eyebrow("Study budget")
        budget = st.slider(
            "Problems you can realistically get through", 10, 200, 60, step=5,
            key="study_budget",
        )

    priority = sorted(chapters, key=lambda c: -(c["weight_pct"] * (1 - c["mastery"])))

    with st.container(border=True):
        eyebrow("Study this, in this order")
        for i, c in enumerate(priority):
            prefix = "🔥 " if i == 0 else f"{i+1}. "
            bg = f"{COLORS['yellow_hi']}30" if i == 0 else "transparent"
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:10px; padding:9px 12px; "
                f"border-radius:8px; background:{bg}; font-family:{FONT_BODY}; font-size:13.5px;'>"
                f"<span style='font-family:{FONT_MONO}; color:{COLORS['ink_muted']}; width:22px;'>{prefix}</span>"
                f"<span style='font-weight:500; flex:0 0 220px;'>{c['name']}</span>"
                f"<span style='font-family:{FONT_MONO}; font-size:11.5px; color:{COLORS['ink_muted']};'>"
                f"{c['weight_pct']}% weight · {c['mastery']*100:.0f}% mastered</span></div>",
                unsafe_allow_html=True,
            )

    # NOTE: this is a placeholder projection curve, not a real simulation.
    # Swap in a real model (e.g. expected-gain-per-problem simulation) later.
    total_weighted_gap = sum(c["weight_pct"] * (1 - c["mastery"]) for c in priority) or 1
    steps = list(range(0, budget + 1, max(5, round(budget / 10))))
    curve_df = pd.DataFrame({
        "budget": steps,
        "focused": [min(95, 48 + (b ** 0.5) * 5.6) for b in steps],
        "even": [min(95, 48 + (b ** 0.5) * 3.4) for b in steps],
    })
    allocation = [
        {
            "name": (c["name"][:15] + "…") if len(c["name"]) > 16 else c["name"],
            "problems": round(budget * (c["weight_pct"] * (1 - c["mastery"])) / total_weighted_gap),
        }
        for c in priority[:6]
    ]

    col1, col2 = st.columns([1.3, 1])
    with col1:
        with st.container(border=True):
            eyebrow("Projected score vs. problems solved")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=curve_df["budget"], y=curve_df["focused"], mode="lines",
                                      name="Focused plan", line=dict(color=COLORS["ballpoint"], width=3)))
            fig.add_trace(go.Scatter(x=curve_df["budget"], y=curve_df["even"], mode="lines",
                                      name="Even split", line=dict(color=COLORS["coral"], width=2, dash="dash")))
            fig.update_layout(**_plotly_base_layout(260),
                               yaxis=dict(range=[0, 100], gridcolor=COLORS["paper_line"]),
                               xaxis=dict(gridcolor=COLORS["paper_line"]),
                               legend=dict(orientation="h", y=-0.25, font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        with st.container(border=True):
            eyebrow("Problems per chapter")
            fig2 = go.Figure(go.Bar(
                x=[a["name"] for a in allocation],
                y=[a["problems"] for a in allocation],
                marker_color=CHAPTER_HUES[: len(allocation)],
            ))
            fig2.update_layout(**_plotly_base_layout(260),
                                xaxis=dict(tickangle=-25, gridcolor=COLORS["paper_line"]),
                                yaxis=dict(gridcolor=COLORS["paper_line"]))
            st.plotly_chart(fig2, use_container_width=True)