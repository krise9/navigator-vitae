"""UI flow uses a fake mail/Auth transport; database authorization is tested in rls.mjs."""
import base64
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest
from engines.supabase_client import validate_public_key


class Query:
    def __init__(self, client, table):
        self.client, self.table = client, table
        self.filters = []
        self.row = None
    def select(self, *a): return self
    def eq(self, key, value): self.filters.append((key, value)); return self
    def limit(self, *a): return self
    def order(self, *a, **k): return self
    def insert(self, row): self.row = row; return self
    def execute(self):
        assert self.client.auth.logged_in
        if self.row is not None:
            self.client.data[self.table].append(self.row)
            return NS(data=[self.row])
        rows = self.client.data[self.table]
        return NS(data=[r for r in rows if all(r.get(k) == v for k,v in self.filters)])


class Auth:
    def __init__(self): self.logged_in = False; self.expired = False; self.requests = []
    def get_session(self): return NS() if self.logged_in else None
    def get_user(self):
        if self.expired: raise ValueError('Expired token')
        assert self.logged_in
        return NS(user=NS(id='synthetic-user', email_confirmed_at='2026-01-01', is_anonymous=False))
    def sign_in_with_password(self, payload):
        self.requests.append(payload)
        if payload['password'] != 'synthetic-test-password': raise ValueError('Invalid password')
        self.logged_in = True
        return NS(session=NS())
    def sign_out(self): self.logged_in = False


class Client:
    def __init__(self):
        self.auth = Auth()
        self.data = {'app_admins': [], 'participants': [{'id':'synthetic-participant', 'auth_user_id':'synthetic-user', 'navigator_id':'TEST-7','first_name':'Tester','last_name':'Fictief','status':'active'}], 'ikigai_runs':[], 'ikigai_responses':[], 'behavior_results':[]}
    def table(self, name): return Query(self, name)
    def rpc(self, name, payload):
        assert self.auth.logged_in
        assert name == 'submit_ikigai'
        assert len(payload['p_answers']) == 20
        self.data['ikigai_runs'].append({'id':'synthetic-run','navigator_id':'TEST-7','module_version':'v1.1.2','status':'completed'})
        return NS(execute=lambda: NS(data='synthetic-run'))


@pytest.fixture
def app():
    clients=[]
    def factory(*a):
        client=Client(); clients.append(client); return client
    with patch('engines.supabase_client.create_client', side_effect=factory):
        at=AppTest.from_file(Path('app.py').resolve(), default_timeout=10)
        at.secrets={'SUPABASE_URL':'https://example.supabase.co','SUPABASE_PUBLISHABLE_KEY':'sb_publishable_synthetic'}
        at.run()
        yield at, clients


def button(at,label): return next(b for b in at.button if b.label == label)
def login(at):
    at.text_input[0].set_value('tester@example.invalid')
    next(x for x in at.text_input if x.label=='Wachtwoord').set_value('synthetic-test-password')
    button(at,'Inloggen').click().run()
    assert not at.exception


def test_full_participant_flow_and_logout(app):
    at,clients=app
    assert len(at.radio)==0
    assert all(x.label != 'Navigator ID' for x in at.text_input)
    login(at)
    at.radio(key='module_choice').set_value('Module 1: Levensrichting').run()
    assert len(at.text_area)==20
    for answer in at.text_area: answer.set_value('Fictief antwoord')
    button(at,'Definitief verzenden').click().run()
    assert len(clients[0].data['ikigai_runs'])==1
    assert not at.exception
    button(at,'← Terug naar overzicht').click().run()
    at.radio(key='module_choice').set_value('Module 2: Denk- en gedragsvoorkeuren').run()
    questions=json.loads(Path('questions/mbti.json').read_text())
    assert len(at.radio)==len(questions)
    for answer in at.radio: answer.set_value('A')
    button(at,'Verzenden').click().run()
    assert len(clients[0].data['behavior_results'])==1
    assert not at.exception
    button(at,'Uitloggen').click().run()
    assert len(at.radio)==0 and len(at.text_area)==0
    assert 'last_result' not in at.session_state
    assert 'last_navigator_id' not in at.session_state
    assert not clients[0].auth.logged_in


def test_wrong_password_and_legacy_state_deny_access(app):
    at,clients=app
    at.session_state['active_module']='ikigai'
    at.session_state['ikigai_navigator_id']='TEST-7'
    at.session_state['ikigai_admin_code']='legacy-code'
    at.session_state['is_admin']=True
    at.run()
    assert len(at.text_area)==0
    at.text_input[0].set_value('tester@example.invalid')
    next(x for x in at.text_input if x.label=='Wachtwoord').set_value('wrong')
    button(at,'Inloggen').click().run()
    assert not clients[0].auth.logged_in
    assert len(at.text_area)==0
    assert at.error


def test_expired_session_clears_answers(app):
    at,clients=app; login(at)
    at.session_state['last_result']={'sensitive':'synthetic'}
    clients[0].auth.expired=True
    at.run()
    assert 'last_result' not in at.session_state
    assert len(at.radio)==0


def test_admin_database_membership_and_existing_profiles(app):
    at,clients=app; login(at)
    clients[0].data['app_admins']=[{'user_id':'synthetic-user'}]
    at.run()
    next(r for r in at.radio if r.label=='Weergave').set_value('Beheer').run()
    assert at.selectbox[0].label=='Dossier'
    at.selectbox[0].set_value(clients[0].data['participants'][0]).run()
    assert not at.exception
    clients[0].data['app_admins']=[]
    at.run()
    assert len(at.selectbox)==0


def test_unlinked_account_is_blocked(app):
    at,clients=app; login(at)
    clients[0].data['participants']=[]
    at.radio(key='module_choice').set_value('Module 1: Levensrichting').run()
    assert len(at.text_area)==0
    assert any('geen actief dossier' in i.value for i in at.info)


@pytest.mark.parametrize('key',['sb_secret_test','invalid', 'a.'+base64.urlsafe_b64encode(json.dumps({'role':'service_role'}).encode()).decode()+'.c'])
def test_privileged_or_invalid_keys_rejected(key):
    with pytest.raises(ValueError): validate_public_key(key)


def test_anon_and_publishable_keys_allowed():
    validate_public_key('sb_publishable_synthetic')
    validate_public_key('a.'+base64.urlsafe_b64encode(json.dumps({'role':'anon'}).encode()).decode()+'.c')
