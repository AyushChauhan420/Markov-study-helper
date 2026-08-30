"""
tabs.py — individual tab view logic: Overview, Chapters, Weighting,
Check-In, and Plan.

The Markov chain engine and adaptive question selection used to live
here as pure client-side functions running off st.session_state. They
now live on the FastAPI backend (backend/engine.py) and are backed by
Supabase, so mastery survives reruns/reloads and question selection is
actually driven by mastery instead of `filtered_questions[:num]`.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from Components import (
    chapter_dot_label,
    eyebrow,
    highlight_span,
    progress_bar,
    stat_chip_row,
    status_pill,
)
from Theme import CHAPTER_HUES, COLORS, FONT_BODY, FONT_DISPLAY, FONT_MONO, bucket_of
from api_client import fetch_adaptive_questions, fetch_plan, submit_answers

SOURCE_LABEL = "AP Calculus AB · official unit weighting"


def _goto(page: str):
    st.session_state.nav_page = page
    st.rerun()


# ---------------------------------------------------------------------
# HOME TAB — landing page, default view on load
# ---------------------------------------------------------------------
def home_tab(chapters):
    total_w = sum(c["weight_pct"] for c in chapters) or 1
    readiness = sum((c["weight_pct"] / total_w) * c["mastery"] * 100 for c in chapters)
    weakest = min(chapters, key=lambda c: c["mastery"])

    with st.container(border=True):
        eyebrow("Welcome")
        st.markdown(
            f"<div style='font-family:{FONT_DISPLAY}; font-size:34px; font-weight:700; "
            f"line-height:1.2; margin-bottom:8px; color:{COLORS['ink']};'>"
            f"Study smarter, not longer.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-family:{FONT_BODY}; font-size:14.5px; color:{COLORS['ink_muted']}; "
            f"line-height:1.7; max-width:640px;'>"
            f"This planner tracks your mastery per chapter, adapts practice question "
            f"difficulty to where you actually stand, and tells you exactly what to "
            f"study next to move your score the most.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True, height=170):
            eyebrow("Projected score")
            st.markdown(
                f"<div style='font-family:{FONT_DISPLAY}; font-size:38px; font-weight:700;'>"
                f"{highlight_span(f'{readiness:.0f}%')}</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"weighted across {len(chapters)} chapters")

    with col2:
        with st.container(border=True, height=170):
            eyebrow("Weakest chapter")
            st.markdown(
                f"<div style='font-family:{FONT_DISPLAY}; font-size:18px; font-weight:600; "
                f"margin-bottom:4px; color:{COLORS['ink']};'>{weakest['name']}</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"{weakest['mastery']*100:.0f}% mastered")
            if st.button("Practice this →", key="home_practice_weakest"):
                st.session_state.checkin_chapter_id = weakest["id"]
                _goto("Practice")

    with col3:
        with st.container(border=True, height=170):
            eyebrow("Get started")
            st.caption("Jump straight to an adaptive practice set or your study plan.")
            if st.button("Start a practice set →", key="home_start_checkin", use_container_width=True):
                _goto("Practice")
            if st.button("View my study plan →", key="home_view_plan", use_container_width=True):
                _goto("Plan")


def _plotly_base_layout(height=280):
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_MONO, color=COLORS["ink_muted"], size=11),
    )


# ---------------------------------------------------------------------
# OVERVIEW TAB — headline numbers only
# ---------------------------------------------------------------------
def overview_tab(chapters):
    total_w = sum(c["weight_pct"] for c in chapters) or 1
    readiness = sum((c["weight_pct"] / total_w) * c["mastery"] * 100 for c in chapters)
    focus_chapter = max(chapters, key=lambda c: c["weight_pct"] * (1 - c["mastery"]))

    BOX_HEIGHT = 230

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True, height=BOX_HEIGHT):
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
        with st.container(border=True, height=BOX_HEIGHT):
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

    with st.container(border=True):
        eyebrow("At a glance")
        counts = {"Solid": 0, "Practicing": 0, "Needs work": 0}
        for c in chapters:
            label, _ = bucket_of(c["mastery"])
            counts[label] += 1
        stat_chip_row(counts)
        st.markdown(
            f"<div style='font-family:{FONT_MONO}; font-size:11px; color:{COLORS['ink_muted']}; "
            f"margin-top:10px;'>Full chapter-by-chapter breakdown lives in the "
            f"<strong style='color:{COLORS['ink']}'>Chapters</strong> tab.</div>",
            unsafe_allow_html=True,
        )


def chapters_tab(chapters):
    with st.container(border=True):
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
                    f"{c['weight_pct']:.0f}% of exam · {c['mastery']*100:.0f}% mastered</span></div>",
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
    col1, col2 = st.columns([1.1, 1])

    with col1:
        with st.container(border=True):
            eyebrow("Adjust chapter weighting")
            for i, c in enumerate(chapters):
                hue = CHAPTER_HUES[i % len(CHAPTER_HUES)]
                chapter_dot_label(c["name"], hue, prefix=f"{c['weight_pct']:.0f}% · ")
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
        with st.container(border=True):
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
# CHECK-IN TAB — adaptive practice set, served + graded by the backend
# ---------------------------------------------------------------------
def checkin_tab(chapters):
    student_id = st.session_state.student_id
    chapter_by_id = {c["id"]: c for c in chapters}
    ids = [c["id"] for c in chapters]
    names = [c["name"] for c in chapters]

    if "checkin_chapter_id" not in st.session_state or st.session_state.checkin_chapter_id not in ids:
        st.session_state.checkin_chapter_id = ids[0]
    st.session_state.setdefault("quiz_answers", {})
    st.session_state.setdefault("quiz_submitted", False)
    st.session_state.setdefault("active_set", None)  # holds the last-fetched adaptive question set
    st.session_state.setdefault("submit_result", None)

    eyebrow("Choose a topic to practice")
    col_topic, col_diff, col_count = st.columns([2, 1.5, 1.5])

    with col_topic:
        current_idx = ids.index(st.session_state.checkin_chapter_id)
        selected_name = st.selectbox("Chapter", names, index=current_idx, key="checkin_chapter_select")
        selected_id = ids[names.index(selected_name)]

    with col_diff:
        difficulty_filter = st.selectbox(
            "Difficulty Level", ["Mixed", "Easy", "Medium", "Hard"], key="checkin_diff_select"
        )

    with col_count:
        num_questions = st.number_input(
            "No. of Questions", min_value=1, max_value=30, value=10, step=1, key="checkin_num_questions"
        )

    if selected_id != st.session_state.checkin_chapter_id:
        st.session_state.checkin_chapter_id = selected_id
        st.session_state.quiz_submitted = False
        st.session_state.quiz_answers = {}
        st.session_state.active_set = None
        st.session_state.submit_result = None
        st.rerun()

    c = chapter_by_id[selected_id]
    hue = CHAPTER_HUES[ids.index(selected_id) % len(CHAPTER_HUES)]
    chapter_dot_label(
        c["name"], hue, suffix=f" · currently {c['mastery']*100:.0f}% mastered · {c['markov_state']}"
    )

    if st.session_state.active_set is None:
        if st.button("🎯 Generate adaptive practice set", type="primary"):
            st.session_state.active_set = fetch_adaptive_questions(
                student_id, selected_id, int(num_questions), difficulty_filter
            )
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.submit_result = None
            st.rerun()
        st.caption(
            "Question difficulty is chosen from your current mastery and Markov "
            "state — low mastery skews easy, high mastery skews hard."
        )
        return

    active_set = st.session_state.active_set
    active_questions = active_set["questions"]
    mix = active_set["difficulty_mix"]
    st.caption(
        f"Adaptive mix for this set (mastery {active_set['mastery']*100:.0f}%, "
        f"state: {active_set['markov_state']}): "
        f"{mix.get('easy', 0)} easy · {mix.get('medium', 0)} medium · {mix.get('hard', 0)} hard"
    )

    if st.session_state.quiz_submitted:
        if st.button("↺ New adaptive set"):
            st.session_state.active_set = None
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.session_state.submit_result = None
            st.rerun()

    for idx, q in enumerate(active_questions):
        qid = q["id"]
        with st.container(border=True):
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

            if st.session_state.quiz_submitted and st.session_state.submit_result:
                result = next(
                    (r for r in st.session_state.submit_result["per_question"] if r["question_id"] == qid), None
                )
                if result:
                    mark_color = COLORS["mint"] if result["correct"] else COLORS["coral"]
                    mark = (
                        "✓ Correct"
                        if result["correct"]
                        else f"✗ Correct answer: {q['options'][result['correct_index']]}"
                    )
                    st.markdown(
                        f"<div style='font-family:{FONT_MONO}; font-size:12px; color:{mark_color};'>{mark}</div>",
                        unsafe_allow_html=True,
                    )

    if not st.session_state.quiz_submitted:
        if st.button("Check my answers →", type="primary"):
            answers = [
                {"question_id": q["id"], "selected_index": st.session_state.quiz_answers.get(q["id"], -1)}
                for q in active_questions
            ]
            result = submit_answers(student_id, selected_id, difficulty_filter, answers)
            st.session_state.submit_result = result
            st.session_state.quiz_submitted = True
            # reflect the new mastery immediately in this tab's chapter object
            c["mastery"] = result["mastery"]
            c["markov_state"] = result["markov_state"]
            st.rerun()
    else:
        result = st.session_state.submit_result
        st.divider()
        eyebrow("Real-Time Standing (Markov Chain Model)")

        col_m1, col_m2 = st.columns([1, 1.5])
        with col_m1:
            st.metric("Score", f"{result['num_correct']}/{result['total']}")
            st.metric("Markov Evaluated State", result["markov_state"])
            st.metric("Updated Mastery", f"{result['mastery']*100:.0f}%")

        with col_m2:
            fig = go.Figure(
                go.Bar(
                    x=["Confused", "Practicing", "Mastered"],
                    y=result["state_probs"],
                    marker=dict(color=[COLORS["coral"], COLORS["amber"], COLORS["mint"]]),
                    text=[f"{p*100:.0f}%" for p in result["state_probs"]],
                    textposition="auto",
                )
            )
            fig.update_layout(**_plotly_base_layout(200), yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------
# PLAN TAB — problem allocation pulled from the backend (mastery-driven)
# ---------------------------------------------------------------------
def plan_tab(chapters):
    student_id = st.session_state.student_id

    with st.container(border=True):
        eyebrow("Study budget")
        budget = st.slider(
            "Problems you can realistically get through", 10, 200, 60, step=5, key="study_budget"
        )

    plan_rows = fetch_plan(student_id, budget)

    with st.container(border=True):
        eyebrow("Study this, in this order")
        for i, c in enumerate(plan_rows):
            prefix = "🔥 " if i == 0 else f"{i+1}. "
            bg = f"{COLORS['yellow_hi']}30" if i == 0 else "transparent"
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:10px; padding:9px 12px; "
                f"border-radius:8px; background:{bg}; font-family:{FONT_BODY}; font-size:13.5px;'>"
                f"<span style='font-family:{FONT_MONO}; color:{COLORS['ink_muted']}; width:22px;'>{prefix}</span>"
                f"<span style='font-family:{FONT_MONO}; font-size:12px; font-weight:600; "
                f"color:{COLORS['ballpoint']}; width:44px;'>{c['weight_pct']:.0f}%</span>"
                f"<span style='font-weight:500; flex:0 0 220px; color:{COLORS['ink']};'>{c['name']}</span>"
                f"<span style='font-family:{FONT_MONO}; font-size:11.5px; color:{COLORS['ink_muted']};'>"
                f"{c['weight_pct']:.0f}% of exam · {c['mastery']*100:.0f}% mastered · "
                f"{c['problems']} problems</span></div>",
                unsafe_allow_html=True,
            )

    total_weighted_gap = sum(c["weight_pct"] * (1 - c["mastery"]) for c in plan_rows) or 1
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
            "problems": c["problems"],
        }
        for c in plan_rows[:6]
    ]

    col1, col2 = st.columns([1.3, 1])
    with col1:
        with st.container(border=True):
            eyebrow("Projected score vs. problems solved")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=curve_df["budget"], y=curve_df["focused"], mode="lines",
                    name="Focused plan", line=dict(color=COLORS["ballpoint"], width=3),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=curve_df["budget"], y=curve_df["even"], mode="lines",
                    name="Even split", line=dict(color=COLORS["coral"], width=2, dash="dash"),
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
        with st.container(border=True):
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
