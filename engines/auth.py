"""Invitation-only email OTP login and database-backed authorization."""
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
    st.write('Meld je aan met het e-mailadres dat bij je uitnodiging hoort.')
    with st.form('request_code', clear_on_submit=True):
        email = st.text_input('E-mailadres').strip().lower()
        requested = st.form_submit_button('Stuur een inlogcode')
    if requested:
        try:
            client.auth.sign_in_with_otp({'email': email, 'options': {'should_create_user': False}})
        except Exception:
            pass  # Same message for unknown email, rate limits and delivery errors.
        st.session_state['_login_email'] = email
        st.info('Als dit adres toegang heeft, ontvang je een code. Controleer ook je spammap. Geen code? Wacht even of neem contact op met de Navigator.')
    if st.session_state.get('_login_email'):
        with st.form('verify_code', clear_on_submit=True):
            token = st.text_input('Eenmalige inlogcode', type='password')
            submitted = st.form_submit_button('Inloggen')
        if submitted:
            try:
                response = client.auth.verify_otp({'email': st.session_state['_login_email'], 'token': token.strip(), 'type': 'email'})
                if not response.session:
                    raise PermissionError('No session')
                get_supabase()
            except Exception:
                clear_session()
                st.error('De code is ongeldig of verlopen. Vraag een nieuwe code aan.')
            else:
                # Keep only the newly authenticated client, discard all prior form state.
                clear_session()
                st.session_state['_auth_client'] = client
                st.rerun()
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
