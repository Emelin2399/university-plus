-- ============================================================
-- UNIVERSITY PLUS — Esquema de base de datos (MVP)
-- PostgreSQL / Supabase
-- ============================================================
-- Ejecutar en el SQL editor de Supabase o con psql.
-- Requiere las extensiones pgcrypto (UUID) y vector (pgvector).
-- ============================================================

create extension if not exists pgcrypto;
create extension if not exists vector;

-- ------------------------------------------------------------
-- Función utilitaria: actualizar updated_at automáticamente
-- ------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- ============================================================
-- 1. PROFILES (extiende auth.users)
-- ============================================================
create table if not exists profiles (
  id          uuid primary key references auth.users (id) on delete cascade,
  full_name   text,
  email       text,
  role        text not null default 'student' check (role in ('student', 'admin')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Crear el perfil automáticamente al registrarse un usuario
create or replace function handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, new.raw_user_meta_data ->> 'full_name')
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- ============================================================
-- 2. SUBJECTS (asignaturas)
-- ============================================================
create table if not exists subjects (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references profiles (id) on delete cascade,
  name        text not null,
  term        text,
  color       text default '#2563eb',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists idx_subjects_user on subjects (user_id);

-- ============================================================
-- 3. DOCUMENTS (material académico)
-- ============================================================
create table if not exists documents (
  id            uuid primary key default gen_random_uuid(),
  subject_id    uuid not null references subjects (id) on delete cascade,
  user_id       uuid not null references profiles (id) on delete cascade,
  name          text not null,
  storage_path  text not null,
  mime_type     text,
  size_bytes    bigint,
  status        text not null default 'pending'
                check (status in ('pending', 'processing', 'ready', 'error')),
  page_count    int,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists idx_documents_subject on documents (subject_id);
create index if not exists idx_documents_user on documents (user_id);

-- ============================================================
-- 4. DOCUMENT_CHUNKS (fragmentos + embeddings para RAG)
-- ============================================================
create table if not exists document_chunks (
  id           uuid primary key default gen_random_uuid(),
  document_id  uuid not null references documents (id) on delete cascade,
  user_id      uuid not null references profiles (id) on delete cascade,
  content      text not null,
  page         int,
  chunk_index  int not null default 0,
  embedding    vector(1536),
  created_at   timestamptz not null default now()
);
create index if not exists idx_chunks_document on document_chunks (document_id);
-- Índice vectorial para búsqueda por similitud de coseno
create index if not exists idx_chunks_embedding
  on document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Función RPC de búsqueda semántica (retrieval del RAG)
create or replace function match_document_chunks(
  query_embedding vector(1536),
  match_count int default 5,
  p_user_id uuid default auth.uid(),
  p_subject_id uuid default null
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  page int,
  similarity float
)
language sql stable as $$
  select
    dc.id,
    dc.document_id,
    dc.content,
    dc.page,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  join documents d on d.id = dc.document_id
  where dc.user_id = p_user_id
    and (p_subject_id is null or d.subject_id = p_subject_id)
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;

-- ============================================================
-- 5. SUMMARIES (resúmenes generados)
-- ============================================================
create table if not exists summaries (
  id           uuid primary key default gen_random_uuid(),
  document_id  uuid not null references documents (id) on delete cascade,
  user_id      uuid not null references profiles (id) on delete cascade,
  content      text not null,
  kind         text not null default 'summary'
               check (kind in ('summary', 'key_concepts', 'glossary')),
  created_at   timestamptz not null default now()
);
create index if not exists idx_summaries_document on summaries (document_id);

-- ============================================================
-- 6. QUIZZES (cuestionarios)
-- ============================================================
create table if not exists quizzes (
  id          uuid primary key default gen_random_uuid(),
  subject_id  uuid not null references subjects (id) on delete cascade,
  user_id     uuid not null references profiles (id) on delete cascade,
  title       text not null,
  config      jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now()
);
create index if not exists idx_quizzes_subject on quizzes (subject_id);

-- ============================================================
-- 7. QUESTIONS (preguntas de un cuestionario)
-- ============================================================
create table if not exists questions (
  id              uuid primary key default gen_random_uuid(),
  quiz_id         uuid not null references quizzes (id) on delete cascade,
  statement       text not null,
  type            text not null default 'multiple_choice'
                  check (type in ('multiple_choice', 'true_false', 'open')),
  options         jsonb,
  correct_answer  text,
  explanation     text,
  position        int not null default 0
);
create index if not exists idx_questions_quiz on questions (quiz_id);

-- ============================================================
-- 8. QUIZ_ATTEMPTS (intentos)
-- ============================================================
create table if not exists quiz_attempts (
  id           uuid primary key default gen_random_uuid(),
  quiz_id      uuid not null references quizzes (id) on delete cascade,
  user_id      uuid not null references profiles (id) on delete cascade,
  score        numeric(5,2),
  started_at   timestamptz not null default now(),
  finished_at  timestamptz
);
create index if not exists idx_attempts_quiz on quiz_attempts (quiz_id);
create index if not exists idx_attempts_user on quiz_attempts (user_id);

-- ============================================================
-- 9. ATTEMPT_ANSWERS (respuestas de cada intento)
-- ============================================================
create table if not exists attempt_answers (
  id            uuid primary key default gen_random_uuid(),
  attempt_id    uuid not null references quiz_attempts (id) on delete cascade,
  question_id   uuid not null references questions (id) on delete cascade,
  given_answer  text,
  is_correct    boolean
);
create index if not exists idx_answers_attempt on attempt_answers (attempt_id);

-- ============================================================
-- 10. ACTIVITIES (tareas, trabajos y exámenes)
-- ============================================================
create table if not exists activities (
  id          uuid primary key default gen_random_uuid(),
  subject_id  uuid not null references subjects (id) on delete cascade,
  user_id     uuid not null references profiles (id) on delete cascade,
  title       text not null,
  due_date    timestamptz,
  status      text not null default 'pending'
              check (status in ('pending', 'in_progress', 'done')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists idx_activities_user on activities (user_id);
create index if not exists idx_activities_due on activities (due_date);

-- ============================================================
-- 11. CHAT_MESSAGES (historial del tutor virtual)
-- ============================================================
create table if not exists chat_messages (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references profiles (id) on delete cascade,
  subject_id  uuid references subjects (id) on delete set null,
  role        text not null check (role in ('user', 'assistant')),
  content     text not null,
  sources     jsonb,
  created_at  timestamptz not null default now()
);
create index if not exists idx_chat_user on chat_messages (user_id);

-- ============================================================
-- 12. STUDY_SESSIONS (registro opcional)
-- ============================================================
create table if not exists study_sessions (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references profiles (id) on delete cascade,
  subject_id        uuid references subjects (id) on delete set null,
  started_at        timestamptz not null default now(),
  duration_minutes  int
);
create index if not exists idx_sessions_user on study_sessions (user_id);

-- ============================================================
-- TRIGGERS updated_at
-- ============================================================
create trigger trg_profiles_updated   before update on profiles   for each row execute function set_updated_at();
create trigger trg_subjects_updated    before update on subjects    for each row execute function set_updated_at();
create trigger trg_documents_updated   before update on documents   for each row execute function set_updated_at();
create trigger trg_activities_updated  before update on activities  for each row execute function set_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY
-- Cada estudiante solo accede a sus propios datos (auth.uid() = user_id)
-- ============================================================
alter table profiles        enable row level security;
alter table subjects        enable row level security;
alter table documents       enable row level security;
alter table document_chunks enable row level security;
alter table summaries       enable row level security;
alter table quizzes         enable row level security;
alter table questions       enable row level security;
alter table quiz_attempts   enable row level security;
alter table attempt_answers enable row level security;
alter table activities      enable row level security;
alter table chat_messages   enable row level security;
alter table study_sessions  enable row level security;

-- profiles: el usuario gestiona su propio perfil
create policy "profiles_self" on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

-- Política genérica "solo mis datos" para tablas con user_id
create policy "subjects_owner"        on subjects        for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "documents_owner"       on documents       for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "chunks_owner"          on document_chunks for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "summaries_owner"       on summaries       for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "quizzes_owner"         on quizzes         for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "attempts_owner"        on quiz_attempts   for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "activities_owner"      on activities      for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "chat_owner"            on chat_messages   for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "sessions_owner"        on study_sessions  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- questions: acceso a través del quiz del usuario
create policy "questions_via_quiz" on questions for all
  using (exists (select 1 from quizzes q where q.id = questions.quiz_id and q.user_id = auth.uid()))
  with check (exists (select 1 from quizzes q where q.id = questions.quiz_id and q.user_id = auth.uid()));

-- attempt_answers: acceso a través del intento del usuario
create policy "answers_via_attempt" on attempt_answers for all
  using (exists (select 1 from quiz_attempts a where a.id = attempt_answers.attempt_id and a.user_id = auth.uid()))
  with check (exists (select 1 from quiz_attempts a where a.id = attempt_answers.attempt_id and a.user_id = auth.uid()));

-- ============================================================
-- FIN DEL ESQUEMA MVP
-- ============================================================
