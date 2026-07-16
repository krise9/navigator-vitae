import streamlit as st
from supabase import Client, create_client


def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


def get_participant(navigator_id: str):
    supabase = get_supabase()

    response = (
        supabase
        .table("participants")
        .select("*")
        .eq("navigator_id", navigator_id.strip())
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None