import pandas as pd
import streamlit as st

from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client
from lib.recommender import generate_recommendations

st.set_page_config(
    page_title="Recommendations | FinPilot AI",
    page_icon="💡",
    layout="wide"
)

st.title("💡 Recommendations")
st.caption("Budget-aware financial intelligence from your transaction behavior.")

user_id = require_auth()
logout_button()

supabase = get_authenticated_supabase_client()


@st.cache_data(ttl=60)
def load_transactions(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("transactions")
        .select("*")
        .eq("user_id", current_user_id)
        .order("date", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=60)
def load_budgets(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("budgets")
        .select("*")
        .eq("user_id", current_user_id)
        .execute()
    )
    return pd.DataFrame(response.data)


transactions_df = load_transactions(user_id)
budgets_df = load_budgets(user_id)

if transactions_df.empty:
    st.info("No transactions found yet.")
    st.stop()

recommendations = generate_recommendations(transactions_df, budgets_df)

if not recommendations:
    st.success("No major financial issues detected right now.")
    st.stop()

high_priority = [r for r in recommendations if r["priority"] == "high"]
medium_priority = [r for r in recommendations if r["priority"] == "medium"]
low_priority = [r for r in recommendations if r["priority"] == "low"]

c1, c2, c3 = st.columns(3)

c1.metric("High Priority", len(high_priority))
c2.metric("Medium Priority", len(medium_priority))
c3.metric("Low Priority", len(low_priority))

st.divider()


def render_card(rec):
    priority = rec.get("priority", "medium")

    if priority == "high":
        icon = "🔴"
    elif priority == "medium":
        icon = "🟡"
    else:
        icon = "🟢"

    with st.container(border=True):
        st.subheader(f"{icon} {rec['title']}")
        st.write(rec["message"])
        st.caption(f"Type: {rec['type']} | Priority: {priority}")


st.subheader("Action Items")

for rec in high_priority:
    render_card(rec)

for rec in medium_priority:
    render_card(rec)

for rec in low_priority:
    render_card(rec)