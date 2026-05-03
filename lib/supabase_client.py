import os
from dotenv import load_dotenv
from supabase import create_client, Client
import streamlit as st

load_dotenv()


def _clean_env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    return value.strip().strip("\"'")


def get_supabase_client() -> Client:
    url = _clean_env_value("SUPABASE_URL")
    key = _clean_env_value("SUPABASE_PUBLISHABLE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be set in the environment")
    return create_client(url, key)

def get_authenticated_supabase_client() -> Client:
    supabase = get_supabase_client()

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if access_token and refresh_token:
        supabase.auth.set_session(access_token, refresh_token)

    return supabase
