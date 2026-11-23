"""Provisioned-account password login and database-backed authorization."""
import streamlit as st

from engines.supabase_client import get_auth_client, get_supabase


def clear_session() -> None:
    # Answers, selected participant, tokens and admin state must never survive logout.
    for key in list(st.session_state):
        del st.session_state[key]


def is_admin() -> bool:
    return bool(get_supabase().table('app_admins').select('user_id').limit(1).execute().data)


def require_login() -> None:
    try:
        client = get_auth_client()
    except Exception:
        st.error('Aanmelden is nog niet beschikbaar. Neem contact op met de Navigator.')
        st.stop()
    if client.auth.get_session():
        try:
            get_supabase()
        except Exception:
            clear_session()
            st.warning('Je sessie is verlopen. Meld je opnieuw aan.')
            st.stop()
        if st.sidebar.button('Uitloggen'):
            try:
                client.auth.sign_out()
            except Exception:
                pass
            finally:
                clear_session()
            st.rerun()
        return

    st.title('Navigator Vitae')
    st.write('Meld je aan met je persoonlijke e-mailadres en wachtwoord.')
    with st.form('password_login', clear_on_submit=True):
        email = st.text_input('E-mailadres').strip().lower()
        password = st.text_input('Wachtwoord', type='password')
        submitted = st.form_submit_button('Inloggen')
    if submitted:
        try:
            response = client.auth.sign_in_with_password({'email': email, 'password': password})
            if not response.session:
                raise PermissionError('No session')
            get_supabase()
        except Exception:
            clear_session()
            st.error('Inloggen is niet gelukt. Controleer je gegevens of probeer het later opnieuw.')
        else:
            clear_session()
            st.session_state['_auth_client'] = client
            st.rerun()
    st.caption('Nog geen account of wachtwoord vergeten? Neem contact op met de Navigator. Er worden tijdens deze testfase geen herstelmails verstuurd.')
    st.stop()


def current_participant():
    client = get_supabase()
    user_id = client.auth.get_user().user.id
    rows = client.table('participants').select('*').eq('auth_user_id', user_id).eq('status', 'active').limit(1).execute().data
    if not rows:
        st.info('Er is nog geen actief dossier aan je account gekoppeld. Neem contact op met de Navigator.')
        st.stop()
    return rows[0]


def render_admin() -> None:
    # Authorization is repeated here; hiding a navigation button is not security.
    if not is_admin():
        raise PermissionError('Administrator required.')
    client = get_supabase()
    st.subheader('Beheer: bestaande dossiers')
    people = client.table('participants').select('id,navigator_id,first_name,last_name').order('navigator_id').execute().data
    if not people:
        st.info('Geen dossiers beschikbaar.')
        return
    person = st.selectbox('Dossier', people, format_func=lambda p: p['navigator_id'], index=None)
    if not person:
        return
    from modules.ikigai import render_existing_answers
    render_existing_answers(person['navigator_id'])
    st.subheader('Gedragsprofielen')
    rows = client.table('behavior_results').select('*').eq('participant_id', person['id']).execute().data
    for row in rows:
        st.write('Type:', row['mbti_type'])
        st.json({k: v for k, v in row.items() if k.endswith('_score') or k.endswith('_position')})
