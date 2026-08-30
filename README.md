# Study Planner

This addresses the organizer feedback directly:

| Feedback | Fix |
|---|---|
| No backend, no database | FastAPI backend (`backend/`) + Supabase Postgres |
| Questions not chosen by mastery/Markov chain, hardcoded | `backend/engine.py`: `pick_difficulty_mix()` turns current mastery + Markov state into an easy/medium/hard question mix, `select_adaptive_questions()` samples from Supabase avoiding recently-seen questions |
| Mastery reset every page reload | Mastery + Markov state now persisted per-student in the `student_mastery` table, updated by `POST /submit` |

## Architecture

```
Streamlit (frontend/)  --HTTP-->  FastAPI (backend/)  --supabase-py-->  Supabase Postgres
```

- **frontend/** — Streamlit UI , only thing that talks to the backend is; `App.py`/`Tabs.py` 
- **backend/** — FastAPI app. `engine.py` holds the Markov chain + adaptive selection logic,
  `database.py` is the Supabase client. `main.py` wires it all into endpoints.
- **Supabase** — `schema.sql` creates 5 tables: `chapters`, `questions`, `students`,
  `student_mastery` (the live BKT/Markov state per student per chapter), `attempts` (full
  answer log, also used to avoid repeating questions).

## Setup

### 1. Supabase
1. Create a project at supabase.com.
2. SQL editor → paste and run `backend/schema.sql`.
3. Project Settings → API → copy the URL and the **service_role** key.

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # fill in SUPABASE_URL / SUPABASE_SERVICE_KEY
python seed.py            # loads chapters.csv + question_bank.csv into Supabase, one-time
uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run App.py
```
By default the frontend points at `http://localhost:8000`. Override with:
```bash
export STUDY_PLANNER_API=https://your-deployed-backend.example.com
```

## How adaptive selection actually works now

1. Student picks a chapter + difficulty filter + count, clicks **Generate adaptive practice set**.
2. Frontend calls `GET /questions/adaptive`.
3. Backend reads the student's current `mastery` + `markov_state` from `student_mastery`
   (defaults to 30% / "Practicing" the first time), and `pick_difficulty_mix()` converts that
   into a distribution, e.g. mastery < 40% → 60% easy / 30% medium / 10% hard.
4. Backend samples questions per that mix from Supabase, preferring ones not in the student's
   last 50 `attempts` for that chapter, and returns them **without** the correct answer index.
5. Student answers, hits **Check my answers**, frontend calls `POST /submit`.
6. Backend grades server-side, logs each answer to `attempts`, runs the same 3-state Markov
   forecast (Confused / Practicing / Mastered) that used to live in the prototype, blends the
   new score into mastery, and **upserts** `student_mastery` — this is what makes progress
   persist instead of vanishing on refresh.
7. `GET /plan` reads that same live mastery to prioritize chapters and allocate a study budget.

## What's unchanged from the prototype

`Theme.py` and `Components.py` (visual styling / small UI helpers) are untouched. The 3-state
Markov transition matrices are the exact ones from the original prototype's
`calculate_markov_standings()` — they just moved to `backend/engine.py` and now read/write real
state instead of a session variable that reset on every reload.
