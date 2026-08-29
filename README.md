# Study Planner

A Streamlit prototype for an exam-readiness / study-priority tool,
styled with a warm "study desk" look (paper background, highlighter
accents) instead of a generic dark dashboard.

## Run it

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Opens at `http://localhost:8501`.

## Project layout

```
study_planner/
├── app.py          entry point — page setup, session state, tab routing
├── theme.py         ← change COLORS / fonts here to restyle the whole app
├── data.py           ← change mock chapters/quiz here to update content
├── components.py     reusable UI pieces (cards, pills, progress bars)
├── tabs.py           the 4 tab views (Overview, Weighting, Check-in, Plan)
└── requirements.txt
```

## How to customize things later

**Change the color scheme** → edit the `COLORS` dict in `theme.py`.
Every component reads from there, so one edit restyles the whole app.

**Change fonts** → edit `FONT_DISPLAY` / `FONT_BODY` / `FONT_MONO` in
`theme.py` (update the Google Fonts `@import` URL too if you pick
different font families).

**Replace the mock data with real data** → edit `data.py`. Keep the
same shape:
```python
{"id": "ch0", "name": "...", "weight_pct": 11, "mastery": 0.62}
```
`get_default_chapters()` can be swapped to load from a database, an
API, or an uploaded file — nothing else in the project needs to
change as long as the shape stays the same.

**Add more quiz questions** → add entries to `QUIZ_BANK` in
`data.py`, keyed by chapter id. Chapters without a quiz entry just
show the self-rating step only.

**Known placeholder**: the "Projected score vs. problems solved"
chart on the Plan tab uses a mock curve, not a real simulation —
see the `NOTE` comment above it in `tabs.py`.
