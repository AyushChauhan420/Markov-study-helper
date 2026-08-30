# Study Planner — ByteSolve

## Architecture

```
Streamlit (frontend/)  --HTTP-->  FastAPI (backend/)  --supabase-py-->  Supabase Postgres
                                          |
                                          `--HTTP-->  Ollama (ai_content.py, "the Fetcher")
```

- **frontend/** — same Streamlit UI as before, but `Data.py` is gone. `api_client.py` is the
  only thing that talks to the backend; `App.py`/`Tabs.py` render whatever it returns.
- **backend/** — FastAPI app. `engine.py` holds the Markov chain + adaptive selection logic
  (moved out of `Tabs.py`, where it used to run client-side against `st.session_state`).
  `database.py` is the Supabase client. `ai_content.py` is the only place that calls the LLM
  ("the Fetcher") — it generates exam syllabi, starter question banks, and diagnostic tests.
  `file_parser.py` extracts text from uploaded PDF/DOCX/TXT files. `main.py` wires it all
  into endpoints.
- **Supabase** — `schema.sql` creates: `exams`, `chapters` (now scoped to an `exam_id`),
  `questions`, `students`, `student_mastery` (live BKT/Markov state per student per chapter),
  `attempts` (answer log, also used to avoid repeating questions), and `diagnostic_sets` /
  `diagnostic_questions` (tests generated from a student's own uploaded material).

## Setup

### 1. Supabase
1. Create a project at supabase.com.
2. SQL editor → paste and run `backend/schema.sql`. (Safe to re-run on top of the old
   schema too — it migrates existing `chapters` rows onto a default `ap-calc-ab` exam.)
3. Project Settings → API → copy the URL and the **service_role** key.

### 2. Ollama
```bash
# install from https://ollama.com, then:
ollama pull llama3.1
ollama serve            # starts the local server on :11434
```

### 3. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # fill in SUPABASE_URL / SUPABASE_SERVICE_KEY / OLLAMA_MODEL if different
python seed.py            # loads chapters.csv + question_bank.csv into Supabase, one-time
uvicorn main:app --reload --port 8000
```
A running Ollama server (with `OLLAMA_MODEL` pulled) is only needed for the exam switcher
and the diagnostic tab — the original AP Calc AB flow (Home/Overview/Chapters/Weighting/
Practice/Plan) works without it once `seed.py` has run.

### 4. Frontend
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
