import streamlit as st
from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client
import os

st.set_page_config(page_title="FinPilot AI", page_icon="💸", layout="wide")

st.title("💸 FinPilot AI")
user_id = require_auth()
logout_button()

supabase = get_authenticated_supabase_client()

st.success(f"Connected as user: {user_id}")

response = (
    supabase
    .table("accounts")
    .select("*")
    .eq("user_id", user_id)
    .execute()
)

st.write(response.data)