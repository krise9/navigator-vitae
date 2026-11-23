"""One Auth client per Streamlit session; never a service-role client."""
import base64
import json

import streamlit as st
from supabase import Client, create_client


def validate_public_key(key: str) -> None:
    if key.startswith('sb_publishable_'):
        return
    try:
        payload = key.split('.')[1]
        role = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))['role']
    except (ValueError, KeyError, IndexError):
        raise ValueError('Configure a Supabase publishable or legacy anon key.') from None
    if role != 'anon':
        raise ValueError('Privileged Supabase keys are forbidden in the application.')


def get_auth_client() -> Client:
    if '_auth_client' not in st.session_state:
        key = st.secrets['SUPABASE_PUBLISHABLE_KEY']
        validate_public_key(key)
        st.session_state['_auth_client'] = create_client(st.secrets['SUPABASE_URL'], key)
    return st.session_state['_auth_client']


def get_supabase() -> Client:
    client = get_auth_client()
    session = client.auth.get_session()
    if not session:
        raise PermissionError('Sign in required.')
    user = client.auth.get_user().user  # server-verified, not user-editable session claims
    if not user or not user.email_confirmed_at or user.is_anonymous:
        raise PermissionError('Verified email required.')
    return client


def get_participant(navigator_id: str):
    response = (get_supabase().table('participants').select('*')
                .eq('navigator_id', navigator_id.strip()).limit(1).execute())
    return response.data[0] if response.data else None
