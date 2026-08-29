-- ============================================================
-- Study Planner — Supabase schema
-- Run this once in Supabase SQL editor (or `psql < schema.sql`)
-- ============================================================

create extension if not exists "pgcrypto";

-- Exam chapters / units, with their exam weighting
create table if not exists chapters (
    id          text primary key,          -- e.g. 'ch0'
    name        text not null,
    weight_pct  numeric not null
);

-- Question bank, seeded from question_bank.csv
create table if not exists questions (
    id              text primary key,      -- e.g. 'ch0_q001'
    chapter_id      text not null references chapters(id) on delete cascade,
    question        text not null,
    option_a        text not null,
    option_b        text not null,
    option_c        text not null,
    option_d        text not null,
    correct_option  text not null check (correct_option in ('a','b','c','d')),
    difficulty      text not null check (difficulty in ('easy','medium','hard'))
);
create index if not exists idx_questions_chapter on questions(chapter_id);
create index if not exists idx_questions_chapter_diff on questions(chapter_id, difficulty);

-- One row per student (anonymous/demo-friendly: just a display name)
create table if not exists students (
    id          uuid primary key default gen_random_uuid(),
    name        text not null default 'Guest',
    created_at  timestamptz not null default now()
);

-- Current mastery / Markov state per (student, chapter). This is the
-- "backend memory" that used to live only in Streamlit session_state.
create table if not exists student_mastery (
    student_id   uuid not null references students(id) on delete cascade,
    chapter_id   text not null references chapters(id) on delete cascade,
    mastery      numeric not null default 0.3,           -- 0..1, BKT-style p(know)
    markov_state text not null default 'Practicing',     -- Confused | Practicing | Mastered
    state_probs  jsonb not null default '[0.2,0.6,0.2]', -- last [confused, practicing, mastered] vector
    updated_at   timestamptz not null default now(),
    primary key (student_id, chapter_id)
);

-- Every question a student has ever answered — this is what makes
-- question selection *adaptive* instead of hardcoded: we exclude
-- recently-seen questions and bias sampling by current mastery.
create table if not exists attempts (
    id              bigint generated always as identity primary key,
    student_id      uuid not null references students(id) on delete cascade,
    chapter_id      text not null references chapters(id),
    question_id     text not null references questions(id),
    selected_option text,
    is_correct      boolean not null,
    difficulty      text not null,
    created_at      timestamptz not null default now()
);
create index if not exists idx_attempts_student_chapter on attempts(student_id, chapter_id);

alter table students enable row level security;
alter table student_mastery enable row level security;
alter table attempts enable row level security;

-- Hackathon-simple policies: service-role key (used by the FastAPI
-- backend) bypasses RLS entirely, so these just stop the anon/public
-- key from reading/writing other people's rows if it's ever exposed.
drop policy if exists "individual access" on students;
create policy "individual access" on students for select using (true);

drop policy if exists "individual mastery access" on student_mastery;
create policy "individual mastery access" on student_mastery for select using (true);

drop policy if exists "individual attempts access" on attempts;
create policy "individual attempts access" on attempts for select using (true);
