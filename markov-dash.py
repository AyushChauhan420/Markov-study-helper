"""
Markov Chain State Dashboard
-----------------------------
Standalone Streamlit + Plotly component that renders an animated,
color-coded bar chart for the 3-state Markov chain output:
    [Confused, Practicing, Mastered]

Run standalone:
    streamlit run markov_dashboard.py

Plug into your team's main app:
    See the "INTEGRATION GUIDE" comment block at the bottom of this file.
"""

import time
import streamlit as st
import plotly.graph_objects as go

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
STATES = ["Confused", "Practicing", "Mastered"]
COLORS = ["#FF4B4B", "#FFB020", "#2ECC71"]   # red -> amber -> green
BG_COLOR = "#0E1117"

st.set_page_config(page_title="Prerequisite State Tracker", layout="centered")


def render_state_chart(probabilities: list[float], key: str = "state_chart", title: str = "Current State Distribution"):
    """
    Renders an animated bar chart for a 3-state probability array.

    Args:
        probabilities: list/array of 3 floats [Confused, Practicing, Mastered].
                        Values should sum to ~1.0 (they'll be normalized just in case).
        key: unique Streamlit key, so you can render multiple charts
             (one per prerequisite topic) on the same page without collisions.
        title: chart title, e.g. "Integration" or "Differential Equations".
    """
    # Defensive normalization in case the backend returns raw weights
    total = sum(probabilities)
    probs = [p / total for p in probabilities] if total > 0 else probabilities

    fig = go.Figure(
        go.Bar(
            x=STATES,
            y=probs,
            marker=dict(
                color=COLORS,
                line=dict(color="rgba(255,255,255,0.15)", width=1.5),
            ),
            text=[f"{p*100:.0f}%" for p in probs],
            textposition="outside",
            textfont=dict(size=18, color="white"),
            width=0.55,
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=22, color="white"), x=0.5),
        yaxis=dict(range=[0, 1.15], showgrid=False, tickfont=dict(color="white"), tickformat=".0%"),
        xaxis=dict(tickfont=dict(size=15, color="white")),
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        showlegend=False,
        margin=dict(t=60, b=30, l=20, r=20),
        height=420,
        transition=dict(duration=700, easing="cubic-in-out"),  # animates bar height changes
    )

    st.plotly_chart(fig, use_container_width=True, key=key)


# ----------------------------------------------------------------------
# STANDALONE DEMO
# (safe to delete this section once you wire in your team's real data)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    st.title("🧠 Prerequisite Mastery Tracker")
    st.caption("Live demo — replace `demo_probabilities` with your Markov chain output.")

    # Simulate what your backend teammates will eventually hand you
    if "demo_probabilities" not in st.session_state:
        st.session_state.demo_probabilities = [0.7, 0.2, 0.1]  # starts "Confused"

    render_state_chart(st.session_state.demo_probabilities, key="demo_chart", title="Integration — State Distribution")

    st.write("Simulate the student solving practice problems:")
    if st.button("✅ Solve a problem (advance state)"):
        c, p, m = st.session_state.demo_probabilities
        # toy transition: shift mass from Confused -> Practicing -> Mastered
        c, p, m = max(c - 0.15, 0), p + 0.05, min(m + 0.10, 1)
        total = c + p + m
        st.session_state.demo_probabilities = [c / total, p / total, m / total]
        st.rerun()

    if st.button("🔄 Reset"):
        st.session_state.demo_probabilities = [0.7, 0.2, 0.1]
        st.rerun()


# ----------------------------------------------------------------------
# INTEGRATION GUIDE — how to plug this into your team's main app
# ----------------------------------------------------------------------
#
# 1. Save this file as `markov_dashboard.py` in your project folder,
#    alongside your team's main Streamlit app file (e.g. `app.py`).
#
# 2. In your team's main app.py, import the render function instead of
#    running this file directly:
#
#       from markov_dashboard import render_state_chart
#
# 3. Wherever your teammates' backend produces the probability array
#    (e.g. `probs = markov_model.get_state_probs(topic="integration")`),
#    just call:
#
#       render_state_chart(probs, key="integration_chart", title="Integration")
#
#    - `probs` must be a list/array of 3 floats: [Confused, Practicing, Mastered]
#    - `key` must be UNIQUE per chart if you show multiple prerequisites
#      on one page (e.g. "integration_chart", "differentiation_chart", ...)
#      Streamlit will throw a duplicate-element error otherwise.
#
# 4. For the chart to visibly ANIMATE when state changes:
#    - Store the probability array in `st.session_state` (see demo above)
#    - After updating it (e.g. after a student answers a diagnostic question
#      or solves a practice problem), call `st.rerun()`
#    - Plotly's `transition` config (already set in this file) will smoothly
#      animate the bars from old height -> new height instead of snapping.
#
# 5. For MULTIPLE prerequisites on one dashboard (e.g. Integration,
#    Differentiation, Limits all feeding into Diff Eq), just loop:
#
#       for topic_name, probs in backend_results.items():
#           render_state_chart(probs, key=f"{topic_name}_chart", title=topic_name)
#
# 6. If your backend pushes updates asynchronously (e.g. via a queue or
#    websocket rather than a button click), wrap the chart render in a
#    `st.empty()` placeholder and update it in a loop with `time.sleep()`
#    between polls — ask if you want that pattern added too.
#
# ----------------------------------------------------------------------