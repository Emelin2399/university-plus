-- ============================================================
-- MIGRACIÓN: adjuntos de las notas (MIS NOTAS PLUS)
-- ------------------------------------------------------------
-- Ejecuta ESTE bloque en el SQL Editor de Supabase si ya habías
-- creado la base de datos con una versión anterior de schema.sql.
-- Es seguro ejecutarlo varias veces (usa "if not exists" y
-- "drop policy if exists").
--
-- Permite adjuntar CUALQUIER tipo de archivo y VARIOS por nota.
-- El archivo se guarda en Supabase Storage (bucket "documents");
-- aquí solo se guarda el metadato.
-- ============================================================

-- 1. Tabla de adjuntos
create table if not exists note_attachments (
  id            uuid primary key default gen_random_uuid(),
  note_id       uuid not null references notes (id) on delete cascade,
  user_id       uuid not null references profiles (id) on delete cascade,
  name          text not null,
  storage_path  text not null,
  mime_type     text,
  size_bytes    bigint,
  created_at    timestamptz not null default now()
);

-- 2. Índice por nota
create index if not exists idx_note_attachments_note on note_attachments (note_id);

-- 3. Seguridad a nivel de fila (cada estudiante solo ve sus adjuntos)
alter table note_attachments enable row level security;

drop policy if exists "note_attachments_owner" on note_attachments;
create policy "note_attachments_owner" on note_attachments
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
