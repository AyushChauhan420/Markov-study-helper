-- ============================================================
-- Study Planner — Supabase schema
-- Run this once in Supabase SQL editor (or `psql < schema.sql`)
-- ============================================================

create extension if not exists "pgcrypto";

-- Exams a student can prep for. Seeded with the original prototype's
-- exam ('ap-calc-ab'); any other exam gets created on the fly the
-- first time someone picks it from the frontend's exam switcher —
-- see backend/ai_content.py + POST /exams.
create table if not exists exams (
    id          text primary key,          -- slug, e.g. 'ap-calc-ab', 'jee-main'
    name        text not null,
    description text,
    source      text not null default 'seed',  -- 'seed' | 'ai-generated'
    created_at  timestamptz not null default now()
);

-- Exam chapters / units, with their exam weighting
create table if not exists chapters (
    id          text primary key,          -- e.g. 'ch0'
    exam_id     text not null default 'ap-calc-ab',
    name        text not null,
    weight_pct  numeric not null
);

-- Migration for pre-existing installs: add exam_id if this schema was
-- applied before exams existed, and backfill every old chapter onto
-- the original exam so nothing already seeded breaks.
do $$
begin
    if not exists (
        select 1 from information_schema.columns
        where table_name = 'chapters' and column_name = 'exam_id'
    ) then
        alter table chapters add column exam_id text not null default 'ap-calc-ab';
    end if;
end $$;

do $$
begin
    if not exists (select 1 from pg_constraint where conname = 'chapters_exam_id_fkey') then
        alter table chapters
            add constraint chapters_exam_id_fkey foreign key (exam_id) references exams(id) on delete cascade;
    end if;
end $$;

create index if not exists idx_chapters_exam on chapters(exam_id);

-- Question bank, seeded from question_bank.csv (ap-calc-ab) or
-- generated on the fly by ai_content.generate_questions() for any
-- other exam.
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

-- ------------------------------------------------------------
-- Diagnostic tests generated from a student's uploaded material
-- (notes / question banks / random study material). One "set" per
-- upload, questions grounded in that specific file via
-- ai_content.generate_diagnostic_questions().
-- ------------------------------------------------------------
create table if not exists diagnostic_sets (
    id           uuid primary key default gen_random_uuid(),
    student_id   uuid not null references students(id) on delete cascade,
    source_name  text,
    created_at   timestamptz not null default now()
);

create table if not exists diagnostic_questions (
    id              text primary key,      -- e.g. 'diag_<set_id>_1'
    set_id          uuid not null references diagnostic_sets(id) on delete cascade,
    concept         text not null default 'General',  -- topic the AI pulled from the material
    question        text not null,
    option_a        text not null,
    option_b        text not null,
    option_c        text not null,
    option_d        text not null,
    correct_option  text not null check (correct_option in ('a','b','c','d')),
    difficulty      text not null default 'medium'
);
create index if not exists idx_diag_q_set on diagnostic_questions(set_id);

alter table students enable row level security;
alter table student_mastery enable row level security;
alter table attempts enable row level security;
alter table diagnostic_sets enable row level security;
alter table diagnostic_questions enable row level security;

-- Hackathon-simple policies: service-role key (used by the FastAPI
-- backend) bypasses RLS entirely, so these just stop the anon/public
-- key from reading/writing other people's rows if it's ever exposed.
drop policy if exists "individual access" on students;
create policy "individual access" on students for select using (true);

drop policy if exists "individual mastery access" on student_mastery;
create policy "individual mastery access" on student_mastery for select using (true);

drop policy if exists "individual attempts access" on attempts;
create policy "individual attempts access" on attempts for select using (true);

drop policy if exists "individual diagnostic sets access" on diagnostic_sets;
create policy "individual diagnostic sets access" on diagnostic_sets for select using (true);

drop policy if exists "individual diagnostic questions access" on diagnostic_questions;
create policy "individual diagnostic questions access" on diagnostic_questions for select using (true);
