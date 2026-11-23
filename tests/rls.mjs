import {PGlite} from '@electric-sql/pglite';
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const db=new PGlite();
await db.exec(readFileSync('tests/schema.sql','utf8'));
// All fixtures are fictitious. Preserve exactly the audited data counts across migration.
await db.exec(`insert into participants(id,navigator_id,first_name) select
 ('10000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,'TEST-'||n,'Synthetic' from generate_series(1,7) n;
insert into ikigai_runs(id,participant_id,navigator_id) select
 ('20000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,
 ('10000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,'TEST-'||n from generate_series(1,4) n;
insert into ikigai_responses(run_id,question_id,answer) select id,'IKI'||lpad(n::text,2,'0'),'Synthetic answer' from ikigai_runs cross join generate_series(1,20) n;
insert into behavior_results(participant_id,navigator_id,mbti_type,e_score,i_score,s_score,n_score,t_score,f_score,j_score,p_score,ie_position,sn_position,tf_position,jp_position)
select id,navigator_id,'INTJ',1,1,1,1,1,1,1,1,50,50,50,50 from participants where navigator_id<>'TEST-7';`);
const tables=['participants','ikigai_runs','ikigai_responses','behavior_results'];
const counts=async()=>Promise.all(tables.map(async t=>(await db.query(`select count(*)::int n from ${t}`)).rows[0].n));
const snapshot=async()=>Promise.all(tables.map(async t=>(await db.query(`select to_jsonb(t) - 'auth_user_id' as row from ${t} t order by id`)).rows));
const originalRows=await snapshot();
const before=await counts();
await db.exec(readFileSync('db/proposed-auth.sql','utf8'));
assert.deepEqual(await snapshot(),originalRows);
assert.deepEqual(await counts(),before); assert.deepEqual(before,[7,4,80,6]);
let passed=1;
const user=n=>`30000000-0000-0000-0000-${String(n).padStart(12,'0')}`;
await db.exec(`insert into auth.users values('${user(1)}'),('${user(2)}'),('${user(7)}'),('${user(8)}'),('${user(9)}');
update participants set auth_user_id='${user(1)}' where navigator_id='TEST-1';
update participants set auth_user_id='${user(2)}' where navigator_id='TEST-2';
update participants set auth_user_id='${user(7)}' where navigator_id='TEST-7';
insert into app_admins values('${user(9)}');`);
async function as(role,id='') {await db.exec(`reset role; set role ${role}; select set_config('request.jwt.claim.sub','${id}',false);`)}
async function denied(sql,params=[]) {await assert.rejects(()=>db.query(sql,params));passed++}
await as('anon');
for (const t of [...tables,'app_admins']) await denied(`select * from ${t}`);
await denied(`select submit_ikigai('TEST-7','{}')`);
await as('authenticated',user(8)); assert.deepEqual(await counts(),[0,0,0,0]);passed++;
await as('authenticated',user(1));assert.deepEqual(await counts(),[1,1,20,1]);passed++;
assert.equal((await db.query("select * from participants where navigator_id='TEST-2'")).rows.length,0);passed++;
await denied(`insert into app_admins values('${user(1)}')`);
await denied(`update participants set auth_user_id='${user(1)}' where navigator_id='TEST-2'`);
await denied(`update ikigai_responses set answer='tampered'`);
await denied(`delete from participants`);
await denied(`insert into ikigai_runs(participant_id,navigator_id) values('10000000-0000-0000-0000-000000000002','TEST-2')`);
await denied(`insert into ikigai_runs(participant_id,navigator_id) values('10000000-0000-0000-0000-000000000001','TEST-2')`);
await denied(`insert into ikigai_responses(run_id,question_id,answer) values('20000000-0000-0000-0000-000000000002','IKI01','tampered')`);
const behaviorInsert=`insert into behavior_results(participant_id,navigator_id,mbti_type,e_score,i_score,s_score,n_score,t_score,f_score,j_score,p_score,ie_position,sn_position,tf_position,jp_position) values($1,$2,'INTJ',1,1,1,1,1,1,1,1,50,50,50,50)`;
await denied(behaviorInsert,['10000000-0000-0000-0000-000000000007','TEST-7']);
await as('authenticated',user(7));
const answers=Object.fromEntries(Array.from({length:20},(_,i)=>['IKI'+String(i+1).padStart(2,'0'),'Synthetic answer']));
await denied('select submit_ikigai($1,$2)', ['TEST-2',JSON.stringify(answers)]);
await denied('select submit_ikigai($1,$2)', ['TEST-7','{"IKI01":"incomplete"}']);
assert.deepEqual(await counts(),[1,0,0,0]);passed++;
// Force a mid-transaction answer failure; verify that no orphan run survives.
await as('postgres'); await db.exec("alter table ikigai_responses add constraint synthetic_failure check(answer <> 'FAIL')");
await as('authenticated',user(7)); await denied('select submit_ikigai($1,$2)',['TEST-7',JSON.stringify({...answers,IKI20:'FAIL'})]);
assert.deepEqual(await counts(),[1,0,0,0]);passed++;
await db.query('select submit_ikigai($1,$2)',['TEST-7',JSON.stringify(answers)]);
await db.query(behaviorInsert,['10000000-0000-0000-0000-000000000007','TEST-7']);
assert.deepEqual(await counts(),[1,1,20,1]);passed++;
await denied('select submit_ikigai($1,$2)',['TEST-7',JSON.stringify(answers)]);
await denied(behaviorInsert,['10000000-0000-0000-0000-000000000007','TEST-7']);
await as('authenticated',user(9));assert.deepEqual(await counts(),[7,5,100,7]);passed++;
assert.equal((await db.query('select * from app_admins')).rows.length,1);passed++;
await as('postgres');await db.exec(`delete from app_admins; update participants set status='paused' where navigator_id='TEST-7'`);
await as('authenticated',user(9));assert.deepEqual(await counts(),[0,0,0,0]);passed++;
await as('authenticated',user(7));assert.deepEqual(await counts(),[0,0,0,0]);passed++;
console.log(`${passed} database assertions passed (real PostgreSQL via PGlite; synthetic data only).`);
await db.close();
