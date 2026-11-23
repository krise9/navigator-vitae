-- Synthetic test schema reflecting the inspected production columns and constraints.
create role anon;
create role authenticated;
create schema auth;
create table auth.users(id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$
 select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid
$$;
grant usage on schema auth,public to anon,authenticated;
grant execute on function auth.uid() to anon,authenticated;
create table participants(id uuid primary key default gen_random_uuid(), navigator_id text unique not null,
 first_name text not null,last_name text,email text,status text not null default 'active',
 created_at timestamptz not null default now(),updated_at timestamptz not null default now(),
 check(status in ('active','paused','completed','archived')));
create table ikigai_runs(id uuid primary key default gen_random_uuid(),participant_id uuid not null references participants(id),
 navigator_id text not null,module_version text not null default 'v1.1.2',status text not null default 'completed',
 started_at timestamptz default now(),submitted_at timestamptz default now());
create table ikigai_responses(id uuid primary key default gen_random_uuid(),run_id uuid not null references ikigai_runs(id) on delete cascade,
 question_id text not null,answer text,created_at timestamptz default now());
create table behavior_results(id uuid primary key default gen_random_uuid(),participant_id uuid not null references participants(id),
 navigator_id text not null,module_version text not null default 'v0.1',mbti_type text not null,
 e_score int not null,i_score int not null,s_score int not null,n_score int not null,t_score int not null,f_score int not null,j_score int not null,p_score int not null,
 ie_position numeric not null,sn_position numeric not null,tf_position numeric not null,jp_position numeric not null,
 submitted_at timestamptz not null default now(),unique(participant_id,module_version));
