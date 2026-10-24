-- BIT Anaerobic Biorefinery: per-user cloud record storage.
-- Apply this migration in Supabase SQL Editor before enabling cloud sync.
create table if not exists public.project_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  record_key text not null check (record_key ~ '^bit[A-Za-z0-9_]{0,120}$'),
  record_value jsonb not null,
  updated_at timestamptz not null default now(),
  constraint project_records_user_key_unique unique (user_id, record_key)
);

create index if not exists project_records_user_updated_idx
  on public.project_records (user_id, updated_at desc);

alter table public.project_records enable row level security;

drop policy if exists "Users can read their own project records" on public.project_records;
create policy "Users can read their own project records"
  on public.project_records for select to authenticated using (auth.uid() = user_id);

drop policy if exists "Users can insert their own project records" on public.project_records;
create policy "Users can insert their own project records"
  on public.project_records for insert to authenticated with check (auth.uid() = user_id);

drop policy if exists "Users can update their own project records" on public.project_records;
create policy "Users can update their own project records"
  on public.project_records for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own project records" on public.project_records;
create policy "Users can delete their own project records"
  on public.project_records for delete to authenticated using (auth.uid() = user_id);

grant select, insert, update, delete on public.project_records to authenticated;
revoke all on public.project_records from anon;

create or replace function public.touch_project_record_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists project_records_updated_at on public.project_records;
create trigger project_records_updated_at before update on public.project_records
for each row execute function public.touch_project_record_updated_at();
