import streamlit as st
from lib.supabase_client import get_supabase_client
import requests


def login_form():
    supabase = get_supabase_client()

    st.sidebar.subheader("Login")

    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            st.session_state["access_token"] = response.session.access_token
            st.session_state["refresh_token"] = response.session.refresh_token
            st.session_state["user_id"] = response.user.id

            st.sidebar.success("Logged in successfully")
            st.rerun()

        except Exception as e:
            st.sidebar.error(f"Login failed: {e}")


def require_auth():
    if "access_token" not in st.session_state:
        login_form()
        st.stop()

    return st.session_state["user_id"]


def logout_button():
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()