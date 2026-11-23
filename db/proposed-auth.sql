-- Reviewed production change: apply only during the approved cutover.
-- Additive: existing IDs, answers and results are preserved. No automatic email matching.
begin;

alter table public.participants add column auth_user_id uuid unique references auth.users(id) on delete restrict;
create table public.app_admins (
  user_id uuid primary key references auth.users(id) on delete cascade
);
alter table public.app_admins enable row level security;
revoke all on public.app_admins from public, anon, authenticated, service_role;
grant select on public.app_admins to authenticated;
create policy admin_self on public.app_admins for select to authenticated
  using (user_id = (select auth.uid()));

-- Do not silently combine these policies with an unknown pre-existing policy.
do $$ begin
  if exists (select 1 from pg_policies where schemaname='public'
    and tablename in ('participants','ikigai_runs','ikigai_responses','behavior_results')) then
    raise exception 'Unexpected existing policies: review before migration';
  end if;
end $$;

alter table public.participants enable row level security;
alter table public.ikigai_runs enable row level security;
alter table public.ikigai_responses enable row level security;
alter table public.behavior_results enable row level security;
revoke all on public.participants, public.ikigai_runs, public.ikigai_responses, public.behavior_results from public, anon, authenticated, service_role;
grant select on public.participants to authenticated;
grant select, insert on public.ikigai_runs, public.ikigai_responses, public.behavior_results to authenticated;

create policy participant_read on public.participants for select to authenticated using (
  (auth_user_id = (select auth.uid()) and status = 'active')
  or exists (select 1 from public.app_admins where user_id = (select auth.uid()))
);
create policy run_read on public.ikigai_runs for select to authenticated using (
  exists (select 1 from public.participants p where p.id = participant_id)
);
create policy run_insert on public.ikigai_runs for insert to authenticated with check (
  exists (select 1 from public.participants p where p.id = participant_id
    and ikigai_runs.module_version = 'v1.1.2' and ikigai_runs.status = 'completed'
    and p.navigator_id = ikigai_runs.navigator_id
    and p.auth_user_id = (select auth.uid()) and p.status = 'active')
);
create policy response_read on public.ikigai_responses for select to authenticated using (
  exists (select 1 from public.ikigai_runs r where r.id = run_id)
);
create policy response_insert on public.ikigai_responses for insert to authenticated with check (
  question_id ~ '^IKI(0[1-9]|1[0-9]|20)$' and nullif(btrim(answer),'') is not null and
  exists (select 1 from public.ikigai_runs r join public.participants p on p.id = r.participant_id
    where r.id = run_id and p.auth_user_id = (select auth.uid()) and p.status = 'active')
);
create policy behavior_read on public.behavior_results for select to authenticated using (
  exists (select 1 from public.participants p where p.id = participant_id)
);
create policy behavior_insert on public.behavior_results for insert to authenticated with check (
  exists (select 1 from public.participants p where p.id = participant_id
    and behavior_results.module_version = 'v0.1'
    and p.navigator_id = behavior_results.navigator_id
    and p.auth_user_id = (select auth.uid()) and p.status = 'active')
);
create unique index ikigai_runs_once on public.ikigai_runs(participant_id,module_version);
create unique index ikigai_answers_once on public.ikigai_responses(run_id,question_id);
create index ikigai_runs_participant_idx on public.ikigai_runs(participant_id);
create index ikigai_responses_run_idx on public.ikigai_responses(run_id);

-- Invoker rights retain all RLS checks. The function makes the two inserts atomic.
create function public.submit_ikigai(p_navigator_id text, p_answers jsonb)
returns uuid language plpgsql security invoker set search_path = '' as $$
declare
  participant uuid;
  new_run uuid;
begin
  if auth.uid() is null then raise exception 'Authentication required'; end if;
  select id into participant from public.participants
    where navigator_id = p_navigator_id and auth_user_id = auth.uid() and status = 'active';
  if participant is null then raise exception 'Access denied'; end if;
  perform pg_advisory_xact_lock(hashtextextended(participant::text, 0));
  if exists (select 1 from public.ikigai_runs where participant_id=participant
    and module_version='v1.1.2' and status='completed') then
    raise exception 'Already completed';
  end if;
  if jsonb_typeof(p_answers) is distinct from 'object' then raise exception 'Invalid answers'; end if;
  if (select count(*) from jsonb_each(p_answers)) <> 20
    or exists (select 1 from jsonb_each(p_answers) a
      where a.key !~ '^IKI(0[1-9]|1[0-9]|20)$' or jsonb_typeof(a.value) <> 'string'
        or length(btrim(a.value #>> '{}')) = 0) then
    raise exception 'All 20 answers required';
  end if;
  insert into public.ikigai_runs(participant_id,navigator_id,module_version,status)
    values(participant,p_navigator_id,'v1.1.2','completed') returning id into new_run;
  insert into public.ikigai_responses(run_id,question_id,answer)
    select new_run,key,value from jsonb_each_text(p_answers);
  return new_run;
end $$;
revoke all on function public.submit_ikigai(text,jsonb) from public, anon, service_role;
grant execute on function public.submit_ikigai(text,jsonb) to authenticated;
commit;
