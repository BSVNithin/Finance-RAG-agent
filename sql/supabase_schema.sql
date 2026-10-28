-- Northstar Investor Pressure Test — Supabase pgvector schema
-- All sample content is fictional. Run in Supabase SQL Editor.
create extension if not exists vector with schema extensions;

create table if not exists public.rag_documents (
  id text primary key,
  document_id text not null,
  source_file text not null,
  document_type text not null,
  quarter text,
  document_date date,
  speaker text,
  section text,
  page_or_timestamp text,
  tags jsonb not null default '[]'::jsonb,
  synthetic boolean not null default true,
  content text not null,
  embedding extensions.vector(1536) not null,
  created_at timestamptz not null default now()
);

create index if not exists rag_documents_embedding_idx
  on public.rag_documents using hnsw (embedding extensions.vector_cosine_ops);

create index if not exists rag_documents_document_id_idx
  on public.rag_documents (document_id);
create index if not exists rag_documents_quarter_idx
  on public.rag_documents (quarter);
create index if not exists rag_documents_type_idx
  on public.rag_documents (document_type);

create or replace function public.match_rag_documents(
  query_embedding extensions.vector(1536),
  match_count int default 5,
  filter_quarter text default null,
  filter_document_type text default null
)
returns table (
  id text,
  document_id text,
  source_file text,
  document_type text,
  quarter text,
  document_date date,
  speaker text,
  section text,
  page_or_timestamp text,
  tags jsonb,
  content text,
  similarity float
)
language sql stable
as $$
  select
    d.id, d.document_id, d.source_file, d.document_type, d.quarter,
    d.document_date, d.speaker, d.section, d.page_or_timestamp,
    d.tags, d.content,
    1 - (d.embedding <=> query_embedding) as similarity
  from public.rag_documents d
  where (filter_quarter is null or d.quarter = filter_quarter or d.quarter = 'multiple' or d.quarter = 'all')
    and (filter_document_type is null or d.document_type = filter_document_type)
  order by d.embedding <=> query_embedding
  limit greatest(1, least(match_count, 10));
$$;

-- Structured rows imported from Excel. Use this for exact numeric filtering and calculations.
create table if not exists public.financial_records (
  id text primary key,
  source_file text not null,
  sheet_name text not null,
  row_number integer not null,
  quarter text,
  row_data jsonb not null,
  search_text text not null,
  imported_at timestamptz not null default now()
);
create index if not exists financial_records_sheet_idx on public.financial_records (sheet_name);
create index if not exists financial_records_quarter_idx on public.financial_records (quarter);
alter table public.financial_records enable row level security;

-- For a classroom prototype, RLS is enabled but direct client access is not granted.
-- Streamlit should call the n8n webhook; keep the Supabase service-role key ONLY in n8n secrets.
alter table public.rag_documents enable row level security;
-- Do not create an anon SELECT/INSERT policy for this table for the demo.
