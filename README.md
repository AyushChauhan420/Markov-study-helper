# Study Planner

A Streamlit prototype for an exam-readiness / study-priority tool.
Five focused tabs (Overview, Chapters, Weighting, Check-in, Plan) keep
each screen to one job, and a sidebar lets you swap between six
accessibility-checked color palettes on the fly.

## Run it

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Opens at `http://localhost:8501`.

## Project layout

```
study_planner/
├── app.py          entry point — palette activation, session state, tab routing, sidebar
├── theme.py         ← palettes, fonts, and global CSS live here
├── data.py           ← change mock chapters/quiz here to update content
├── components.py     reusable UI pieces (cards, pills, progress bars, stat chips)
├── tabs.py           the 5 tab views (Overview, Chapters, Weighting, Check-in, Plan)
└── requirements.txt
```

## Tabs

- **Overview** — only the headline numbers: overall readiness score,
  biggest opportunity chapter, and a 3-chip status summary (Solid /
  Practicing / Needs work). Deliberately minimal for a first-time user.
- **Chapters** — the full chapter-by-chapter breakdown (progress bars,
  mastery %, exam weight) that used to live in Overview.
- **Weighting** — adjust how much each chapter counts toward the exam.
- **Check-in** — take a practice set per chapter; updates mastery and
  shows the Markov-chain standing forecast.
- **Plan** — priority order and a suggested problems-per-chapter split
  for a given study budget.

## Color palettes

Pick a palette from the sidebar — it applies everywhere instantly (no
reload). All six are tuned so body text and status colors hold at
least WCAG AA contrast against their background:

| Palette | Feel |
|---|---|
| Study Desk | Warm paper & ink, highlighter accents (default) |
| Slate Minimal | Cool neutral gray, indigo accent — modern SaaS |
| Midnight | Dark mode — soft blue glow on near-black |
| Sage & Clay | Earthy sage & terracotta, soft and calm |
| Nordic Frost | Cool blue-gray, crisp and quiet |
| Sunset Pop | Cream base, punchy magenta & gold accents |


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
