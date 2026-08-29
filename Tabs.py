"""
tabs.py — individual tab view logic including Overview, Weighting, Check-In (up to 100 questions),
and Plan tabs, integrated with the real-time Markov chain standing tracker.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from Components import (
    chapter_dot_label,
    eyebrow,
    highlight_span,
    progress_bar,
    status_pill,
)
from Data import QUESTION_BANK, SOURCE_LABEL
from Theme import CHAPTER_HUES, COLORS, FONT_BODY, FONT_DISPLAY, FONT_MONO


def _plotly_base_layout(height=280):
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_MONO, color=COLORS["ink_muted"], size=11),
    )


# ---------------------------------------------------------------------
# MARKOV CHAIN ENGINE
# ---------------------------------------------------------------------
def calculate_markov_standings(completed: int, total_requested: int, difficulty: str, current_mastery: float):
    """
    Computes real-time student standing using a 3-State Markov Chain Model:
    States: [Confused, Practicing, Mastered]
    Updates state transition probability matrix based on user accuracy and chosen difficulty.
    """
    if total_requested <= 0:
        return "Practicing", [0.2, 0.6, 0.2]

    accuracy = completed / float(total_requested)

    diff_weights = {"easy": 0.8, "medium": 1.0, "hard": 1.3, "mixed": 1.0}
    weight = diff_weights.get(difficulty.lower(), 1.0)
    adjusted_performance = min(1.0, accuracy * weight)

    # Initial probability vector v0 based on chapter mastery
    v0 = np.array([max(0.0, 1.0 - current_mastery), current_mastery * 0.5, current_mastery * 0.5])
    v0 = v0 / np.sum(v0)

    # Transition probability matrix (P) based on test performance
    if adjusted_performance >= 0.75:
        P = np.array([[0.1, 0.3, 0.6], [0.05, 0.25, 0.70], [0.0, 0.1, 0.9]])
    elif adjusted_performance >= 0.4:
        P = np.array([[0.3, 0.5, 0.2], [0.15, 0.60, 0.25], [0.05, 0.35, 0.60]])
    else:
        P = np.array([[0.7, 0.2, 0.1], [0.40, 0.50, 0.10], [0.20, 0.50, 0.30]])

    # 3-step forecast matrix multiplication
    v_future = v0 @ np.linalg.matrix_power(P, 3)
    states = ["Confused", "Practicing", "Mastered"]
    current_state = states[int(np.argmax(v_future))]

    return current_state, v_future.tolist()


# ---------------------------------------------------------------------
# OVERVIEW TAB
# ---------------------------------------------------------------------
def overview_tab(chapters):
    total_w = sum(c["weight_pct"] for c in chapters) or 1
    readiness = sum((c["weight_pct"] / total_w) * c["mastery"] * 100 for c in chapters)
    focus_chapter = max(chapters, key=lambda c: c["weight_pct"] * (1 - c["mastery"]))

    col1, col2 = st.columns([1.1, 1])

    with col1:
        with st.container():
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
        with st.container():
            eyebrow("Biggest opportunity")
            st.markdown(
                f"<div style='font-family:{FONT_DISPLAY}; font-size:20px; font-weight:600; "
                f"margin-bottom:6px; color:{COLORS['ink']};'>{focus_chapter['name']}</div>",
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

    with st.container():
        eyebrow("Chapter breakdown")
        sorted_chapters = sorted(chapters, key=lambda c: -c["weight_pct"])
        for i, c in enumerate(sorted_chapters):
            row_l, row_r = st.columns([5, 1])
            with row_l:
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'>"
                    f"<span style='font-family:{FONT_BODY}; font-size:13.5px; font-weight:500; "
                    f"color:{COLORS['ink']};'>{c['name']}</span>"
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
        with st.container():
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
                hue = CHAPTER_HUES[i % len(CHAPTER_HUES)]
                chapter_dot_label(c["name"], hue, suffix=f" · {pct:.0f}%")
                new_w = st.slider(
                    f"{c['name']} weight",
                    min_value=1.0,
                    max_value=30.0,
                    value=float(c["weight_pct"]),
                    step=0.5,
                    key=f"weight_{c['id']}",
                    label_visibility="collapsed",
                )
                c["weight_pct"] = new_w

    with col2:
        with st.container():
            eyebrow("Exam weight distribution")
            fig = go.Figure(
                go.Pie(
                    labels=[c["name"] for c in chapters],
                    values=[c["weight_pct"] for c in chapters],
                    hole=0.55,
                    marker=dict(colors=CHAPTER_HUES[: len(chapters)], line=dict(color=COLORS["card"], width=2)),
                    textinfo="none",
                )
            )
            fig.update_layout(**_plotly_base_layout(300), legend=dict(font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------
# CHECK-IN TAB
# ---------------------------------------------------------------------
def checkin_tab(chapters):
    chapter_by_id = {c["id"]: c for c in chapters}
    ids = [c["id"] for c in chapters]
    names = [c["name"] for c in chapters]

    if "checkin_chapter_id" not in st.session_state or st.session_state.checkin_chapter_id not in ids:
        st.session_state.checkin_chapter_id = ids[0]
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    eyebrow("Choose a topic to practice")
    col_topic, col_diff, col_count = st.columns([2, 1.5, 1.5])

    with col_topic:
        current_idx = ids.index(st.session_state.checkin_chapter_id)
        selected_name = st.selectbox("Chapter", names, index=current_idx, key="checkin_chapter_select")
        selected_id = ids[names.index(selected_name)]

    all_questions = QUESTION_BANK.get(selected_id, [])

    with col_diff:
        difficulty_filter = st.selectbox(
            "Difficulty Level", ["Mixed", "Easy", "Medium", "Hard"], key="checkin_diff_select"
        )

    # Filter questions matching selected difficulty
    if difficulty_filter != "Mixed":
        filtered_questions = [
            q for q in all_questions if str(q.get("difficulty", "")).lower() == difficulty_filter.lower()
        ]
        if len(filtered_questions) < len(all_questions):
            remaining = [q for q in all_questions if q not in filtered_questions]
            filtered_questions.extend(remaining)
    else:
        filtered_questions = all_questions

    available_total = max(1, min(len(filtered_questions), 100))

    with col_count:
        num_questions = st.number_input(
            f"No. of Questions (Max {available_total})",
            min_value=1,
            max_value=available_total,
            value=min(10, available_total),
            step=1,
            key="checkin_num_questions",
        )

    if selected_id != st.session_state.checkin_chapter_id:
        st.session_state.checkin_chapter_id = selected_id
        st.session_state.quiz_submitted = False
        st.session_state.quiz_answers = {}
        st.rerun()

    c = chapter_by_id[selected_id]
    hue = CHAPTER_HUES[ids.index(selected_id) % len(CHAPTER_HUES)]
    chapter_dot_label(
        c["name"], hue, suffix=f" · {available_total} total questions available"
    )

    active_questions = filtered_questions[: int(num_questions)]

    if st.session_state.quiz_submitted:
        if st.button("↺ Retake practice set"):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.rerun()

    for idx, q in enumerate(active_questions):
        qid = q["id"]
        with st.container():
            st.markdown(
                f"<div style='font-family:{FONT_BODY}; font-size:13.5px; margin-bottom:6px; color:{COLORS['ink']};'>"
                f"<strong>Q{idx+1} [{q.get('difficulty', 'medium').capitalize()}]</strong> {q['question']}</div>",
                unsafe_allow_html=True,
            )
            selected = st.radio(
                "options",
                q["options"],
                key=f"quiz_{qid}",
                label_visibility="collapsed",
                horizontal=True,
                disabled=st.session_state.quiz_submitted,
            )
            if selected is not None:
                st.session_state.quiz_answers[qid] = q["options"].index(selected)
            if st.session_state.quiz_submitted:
                is_correct = st.session_state.quiz_answers.get(qid) == q["correct_index"]
                mark_color = COLORS["mint"] if is_correct else COLORS["coral"]
                mark = "✓ Correct" if is_correct else f"✗ Correct answer: {q['options'][q['correct_index']]}"
                st.markdown(
                    f"<div style='font-family:{FONT_MONO}; font-size:12px; color:{mark_color};'>{mark}</div>",
                    unsafe_allow_html=True,
                )

    if not st.session_state.quiz_submitted:
        if st.button("Check my answers →", type="primary"):
            num_correct = sum(
                1 for q in active_questions if st.session_state.quiz_answers.get(q["id"]) == q["correct_index"]
            )
            score_frac = num_correct / len(active_questions)
            c["mastery"] = round(min(0.97, max(0.05, 0.1 + 0.85 * score_frac)), 3)
            st.session_state.quiz_submitted = True
            st.rerun()
    else:
        num_correct = sum(
            1 for q in active_questions if st.session_state.quiz_answers.get(q["id"]) == q["correct_index"]
        )

        standing_state, probs = calculate_markov_standings(
            num_correct, len(active_questions), difficulty_filter, c["mastery"]
        )

        st.divider()
        eyebrow("Real-Time Standing (Markov Chain Model)")

        col_m1, col_m2 = st.columns([1, 1.5])
        with col_m1:
            st.metric("Score", f"{num_correct}/{len(active_questions)}")
            st.metric("Markov Evaluated State", standing_state)

        with col_m2:
            fig = go.Figure(
                go.Bar(
                    x=["Confused", "Practicing", "Mastered"],
                    y=probs,
                    marker=dict(color=[COLORS["coral"], COLORS["amber"], COLORS["mint"]]),
                    text=[f"{p*100:.0f}%" for p in probs],
                    textposition="auto",
                )
            )
            fig.update_layout(**_plotly_base_layout(200), yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------
# PLAN TAB
# ---------------------------------------------------------------------
def plan_tab(chapters):
    with st.container():
        eyebrow("Study budget")
        budget = st.slider(
            "Problems you can realistically get through", 10, 200, 60, step=5, key="study_budget"
        )

    priority = sorted(chapters, key=lambda c: -(c["weight_pct"] * (1 - c["mastery"])))

    with st.container():
        eyebrow("Study this, in this order")
        for i, c in enumerate(priority):
            prefix = "🔥 " if i == 0 else f"{i+1}. "
            bg = f"{COLORS['yellow_hi']}30" if i == 0 else "transparent"
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:10px; padding:9px 12px; "
                f"border-radius:8px; background:{bg}; font-family:{FONT_BODY}; font-size:13.5px;'>"
                f"<span style='font-family:{FONT_MONO}; color:{COLORS['ink_muted']}; width:22px;'>{prefix}</span>"
                f"<span style='font-weight:500; flex:0 0 220px; color:{COLORS['ink']};'>{c['name']}</span>"
                f"<span style='font-family:{FONT_MONO}; font-size:11.5px; color:{COLORS['ink_muted']};'>"
                f"{c['weight_pct']}% weight · {c['mastery']*100:.0f}% mastered</span></div>",
                unsafe_allow_html=True,
            )

    total_weighted_gap = sum(c["weight_pct"] * (1 - c["mastery"]) for c in priority) or 1
    steps = list(range(0, budget + 1, max(5, round(budget / 10))))
    curve_df = pd.DataFrame(
        {
            "budget": steps,
            "focused": [min(95, 48 + (b**0.5) * 5.6) for b in steps],
            "even": [min(95, 48 + (b**0.5) * 3.4) for b in steps],
        }
    )
    allocation = [
        {
            "name": (c["name"][:15] + "…") if len(c["name"]) > 16 else c["name"],
            "problems": round(budget * (c["weight_pct"] * (1 - c["mastery"])) / total_weighted_gap),
        }
        for c in priority[:6]
    ]

    col1, col2 = st.columns([1.3, 1])
    with col1:
        with st.container():
            eyebrow("Projected score vs. problems solved")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=curve_df["budget"],
                    y=curve_df["focused"],
                    mode="lines",
                    name="Focused plan",
                    line=dict(color=COLORS["ballpoint"], width=3),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=curve_df["budget"],
                    y=curve_df["even"],
                    mode="lines",
                    name="Even split",
                    line=dict(color=COLORS["coral"], width=2, dash="dash"),
                )
            )
            fig.update_layout(
                **_plotly_base_layout(260),
                yaxis=dict(range=[0, 100], gridcolor=COLORS["paper_line"]),
                xaxis=dict(gridcolor=COLORS["paper_line"]),
                legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        with st.container():
            eyebrow("Problems per chapter")
            fig2 = go.Figure(
                go.Bar(
                    x=[a["name"] for a in allocation],
                    y=[a["problems"] for a in allocation],
                    marker_color=CHAPTER_HUES[: len(allocation)],
                )
            )
            fig2.update_layout(
                **_plotly_base_layout(260),
                xaxis=dict(tickangle=-25, gridcolor=COLORS["paper_line"]),
                yaxis=dict(gridcolor=COLORS["paper_line"]),
            )
            st.plotly_chart(fig2, use_container_width=True)
