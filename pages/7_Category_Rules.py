from math import log

from numpy import require
import streamlit as st
import pandas as pd
from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client

st.set_page_config(
    page_title="Category Rules | FinPilot AI",
    page_icon="🏷️",
    layout="wide"
)

st.title("🏷️Category Rules")
st.caption("Manage personalized merchant/category learning rules.")

user_id = require_auth()
logout_button()

supabase = get_authenticated_supabase_client()

CATEGORIES = [
    "Income",
    "Groceries",
    "Dining",
    "Transportation",
    "Housing",
    "Utilities",
    "Subscriptions",
    "Shopping",
    "Healthcare",
    "Education",
    "Travel",
    "Entertainment",
    "Savings",
    "Debt",
    "Uncategorized",
]

@st.cache_data(ttl=60)
def load_rules(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("category_rules")
        .select("*")
        .eq("user_id", current_user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)

def upsert_rule(keyword: str, category: str):
    payload = {
        "user_id": user_id,
        "keyword": keyword.lower().strip(),
        "category": category,
    }

    return (
        supabase
        .table("category_rules")
        .upsert(payload, on_conflict="user_id, keyword")
        .execute()
    )

def delete_rule(rule_id: str):
    return(
        supabase
        .table("category_rules")
        .delete()
        .eq("id", rule_id)
        .eq("user_id", user_id)
        .execute()
    )

st.subheader("Add / Update Rule")

with st.form("rule_form"):
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("Keyword or merchant",
                                placeholder="Example: starbucks, amazon, uber eats")
        
    with col2:
        category = st.selectbox("Category", CATEGORIES)

    submitted = st.form_submit_button("Save Rule")

    if submitted:
        if not keyword.strip():
            st.error("Keyword is required.")
        else:
            try:
                upsert_rule(keyword, category)
                st.cache_data.clear()
                st.success("Rule saved successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save rule: {str(e)}")

st.divider()
rules_df = load_rules(user_id)
st.subheader("Saved Rules")
if rules_df.empty:
    st.info("No category rules created yet.")
    st.stop()

st.dataframe(
    rules_df[["keyword", "category", "created_at"]],
    width="stretch",
    hide_index=True
)

st.divider()

rule_options = {
    f"{row['keyword']} → {row['category']}": row["id"]
    for _, row in rules_df.iterrows()
}

selected_rule = st.selectbox(
    "Select rule to delete",
    options=list(rule_options.keys())
)

if st.button("Delete Selected Rule"):
    try:
        delete_rule(rule_options[selected_rule])
        st.cache_data.clear()
        st.success("Rule deleted successfully.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to delete rule: {e}")
