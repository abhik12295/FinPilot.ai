import pandas as pd
import plotly.express as px
import streamlit as st

from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client

st.set_page_config(
    page_title="FinPilot AI",
    page_icon="💸",
    layout="wide"
)

st.title("💸 FinPilot AI")
st.caption("Your autonomous personal finance planner")

user_id = require_auth()
logout_button()

supabase = get_authenticated_supabase_client()


@st.cache_data(ttl=60)
def load_accounts(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("accounts")
        .select("*")
        .eq("user_id", current_user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)


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


accounts_df = load_accounts(user_id)
transactions_df = load_transactions(user_id)

if accounts_df.empty:
    st.info("No accounts found yet. Use the Seed Test Data page or connect SimpleFIN later.")
    st.stop()

if transactions_df.empty:
    st.info("No transactions found yet. Use the Seed Test Data page or connect SimpleFIN later.")
    st.stop()

transactions_df["date"] = pd.to_datetime(transactions_df["date"])
transactions_df["amount"] = pd.to_numeric(transactions_df["amount"], errors="coerce").fillna(0)

current_month = pd.Timestamp.today().month
current_year = pd.Timestamp.today().year

monthly_df = transactions_df[
    (transactions_df["date"].dt.month == current_month)
    & (transactions_df["date"].dt.year == current_year)
].copy()

spending_df = monthly_df[monthly_df["amount"] < 0].copy()
income_df = monthly_df[monthly_df["amount"] > 0].copy()

spending_df["spend_amount"] = spending_df["amount"].abs()

total_balance = accounts_df["balance"].sum()
monthly_spending = spending_df["spend_amount"].sum()
monthly_income = income_df["amount"].sum()
net_cash_flow = monthly_income - monthly_spending

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Balance", f"${total_balance:,.2f}")
col2.metric("Monthly Income", f"${monthly_income:,.2f}")
col3.metric("Monthly Spending", f"${monthly_spending:,.2f}")
col4.metric("Net Cash Flow", f"${net_cash_flow:,.2f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Spending by Category")

    if spending_df.empty:
        st.info("No spending transactions for this month.")
    else:
        category_summary = (
            spending_df
            .groupby("category", as_index=False)["spend_amount"]
            .sum()
            .sort_values("spend_amount", ascending=False)
        )

        fig = px.pie(
            category_summary,
            names="category",
            values="spend_amount",
            hole=0.45
        )

        st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Daily Spending")

    if spending_df.empty:
        st.info("No daily spending found.")
    else:
        daily_summary = (
            spending_df
            .groupby("date", as_index=False)["spend_amount"]
            .sum()
            .sort_values("date")
        )

        fig = px.bar(
            daily_summary,
            x="date",
            y="spend_amount",
            labels={
                "date": "Date",
                "spend_amount": "Spending"
            }
        )

        st.plotly_chart(fig, width="stretch")

st.divider()

st.subheader("Accounts")

st.dataframe(
    accounts_df[["name", "type", "balance", "currency", "updated_at"]],
    width="stretch"
)

st.subheader("Recent Transactions")

display_cols = [
    "date",
    "merchant",
    "description",
    "amount",
    "category",
    "pending"
]

st.dataframe(
    transactions_df[display_cols],
    width="stretch",
    hide_index=True
)