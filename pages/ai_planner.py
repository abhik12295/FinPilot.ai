from select import select

import pandas as pd
import streamlit as st

from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client
from lib.ai_engine import ask_finpilot_ai

st.set_page_config(
    page_title="AI Planner | FinPilot AI",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI Planner")
st.caption("A rule-based financial planner. Later we will upgrade this with OpenAI or Ollama.")

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
def load_accounts(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("accounts")
        .select("*")
        .eq("user_id", current_user_id)
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


@st.cache_data(ttl=60)
def load_subscriptions(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("subscriptions")
        .select("*")
        .eq("user_id", current_user_id)
        .execute()
    )
    return pd.DataFrame(response.data)
def generate_finance_summary(accounts_df: pd.DataFrame, transactions_df: pd.DataFrame) -> str:
    if transactions_df.empty:
        return "No transaction data is available yet."

    df = transactions_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    current_month = pd.Timestamp.today().month
    current_year = pd.Timestamp.today().year

    monthly_df = df[
        (df["date"].dt.month == current_month)
        & (df["date"].dt.year == current_year)
    ].copy()

    income = monthly_df[monthly_df["amount"] > 0]["amount"].sum()
    spending_df = monthly_df[monthly_df["amount"] < 0].copy()
    spending_df["spend"] = spending_df["amount"].abs()
    spending = spending_df["spend"].sum()

    net_cash_flow = income - spending
    total_balance = accounts_df["balance"].sum() if not accounts_df.empty else 0

    if not spending_df.empty:
        top_category = (
            spending_df.groupby("category")["spend"]
            .sum()
            .sort_values(ascending=False)
        )
        top_category_name = top_category.index[0]
        top_category_amount = top_category.iloc[0]
    else:
        top_category_name = "None"
        top_category_amount = 0

    savings_rate = (net_cash_flow / income * 100) if income > 0 else 0

    summary = f"""
        ### Daily Finance Summary

        Your current total balance is ${total_balance:,.2f}.

        This month, you have recorded ${income:,.2f} in income and ${spending:,.2f} in spending.

        Your estimated net cash flow is ${net_cash_flow:,.2f}.

        Your top spending category is **{top_category_name}**, with **${top_category_amount:,.2f}** spent.

        Your estimated savings rate is **{savings_rate:.1f}%**.
        """

    if savings_rate >= 20:
        summary += "\n✅ Your savings rate looks healthy based on the current data."
    elif income > 0:
        summary += "\n⚠️ Your savings rate is below the common 20% target. Consider reviewing discretionary categories."
    else:
        summary += "\nℹ️ No income was detected for this month yet, so savings rate may not be reliable."

    return summary


accounts_df = load_accounts(user_id)

# month selection
transactions_df = load_transactions(user_id)
transactions_df['date'] = pd.to_datetime(transactions_df['date'])
available_months = (
    transactions_df["date"].dt.to_period("M")
    .astype(str)
    .sort_values(ascending=False)
    .unique()
)

selected_month = st.selectbox(
    "Select analysis month",
    options=available_months
)


budgets_df = load_budgets(user_id)
subscriptions_df = load_subscriptions(user_id)
selected_period = pd.Period(selected_month)
filtered_transactions_df = transactions_df[
    transactions_df["date"].dt.to_period("M") == selected_period
].copy()


summary = generate_finance_summary(accounts_df, filtered_transactions_df)

st.markdown(summary)

st.divider()
st.divider()

st.subheader("Ask FinPilot AI")

question = st.text_input(
    "Ask a finance question",
    placeholder="Example: Can I afford a $500 purchase this month?"
)

if st.button("Ask AI"):
    if not question:
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("FinPilot AI is thinking..."):
                answer = ask_finpilot_ai(
                    question=question,
                    accounts_df=accounts_df,
                    transactions_df=filtered_transactions_df,
                    budgets_df=budgets_df,
                    subscriptions_df=subscriptions_df,
                )

            st.markdown(answer)

        except Exception as e:
            st.error(f"AI request failed: {e}")