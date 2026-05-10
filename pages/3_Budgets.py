import pandas as pd
import streamlit as st

from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client

st.set_page_config(
    page_title="Budgets | FinPilot AI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Budgets")
st.caption("Create monthly category budgets and track spending utilization.")

user_id = require_auth()
logout_button()

supabase = get_authenticated_supabase_client()

CATEGORIES = [
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
def load_budgets(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("budgets")
        .select("*")
        .eq("user_id", current_user_id)
        .order("category")
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
        .execute()
    )
    return pd.DataFrame(response.data)


def upsert_budget(category: str, monthly_limit: float):
    payload = {
        "user_id": user_id,
        "category": category,
        "monthly_limit": monthly_limit,
    }

    return (
        supabase
        .table("budgets")
        .upsert(payload, on_conflict="user_id,category")
        .execute()
    )


budgets_df = load_budgets(user_id)
transactions_df = load_transactions(user_id)

st.subheader("Add or Update Budget")

with st.form("budget_form"):
    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox("Category", CATEGORIES)

    with col2:
        monthly_limit = st.number_input(
            "Monthly limit ($)",
            min_value=0.0,
            step=25.0,
            format="%.2f"
        )

    submitted = st.form_submit_button("Save Budget")

    if submitted:
        if monthly_limit <= 0:
            st.error("Monthly limit must be greater than 0.")
        else:
            try:
                upsert_budget(category, monthly_limit)
                st.cache_data.clear()
                st.success(f"Budget saved for {category}.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save budget: {e}")

st.divider()

st.subheader("Budget Utilization")

if budgets_df.empty:
    st.info("No budgets created yet.")
    st.stop()

if transactions_df.empty:
    st.info("No transactions found yet.")
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
spending_df["spent"] = spending_df["amount"].abs()

category_spend = (
    spending_df
    .groupby("category", as_index=False)["spent"]
    .sum()
)

budget_view = budgets_df.merge(
    category_spend,
    on="category",
    how="left"
)

budget_view["spent"] = budget_view["spent"].fillna(0)
budget_view["remaining"] = budget_view["monthly_limit"] - budget_view["spent"]
budget_view["utilization_pct"] = (
    budget_view["spent"] / budget_view["monthly_limit"] * 100
).round(2)

budget_view["status"] = budget_view["utilization_pct"].apply(
    lambda x: "Over Budget" if x > 100 else "Warning" if x >= 80 else "Healthy"
)

m1, m2, m3 = st.columns(3)

m1.metric("Budgets", len(budget_view))
m2.metric("Over Budget", int((budget_view["status"] == "Over Budget").sum()))
m3.metric("Warning", int((budget_view["status"] == "Warning").sum()))

for _, row in budget_view.iterrows():
    with st.container(border=True):
        left, right = st.columns([3, 1])

        with left:
            st.subheader(row["category"])
            st.progress(min(float(row["utilization_pct"]) / 100, 1.0))
            st.write(
                f"Spent ${row['spent']:,.2f} of ${row['monthly_limit']:,.2f} "
                f"({row['utilization_pct']:,.2f}%)"
            )

        with right:
            st.metric("Remaining", f"${row['remaining']:,.2f}")
            st.caption(row["status"])

st.divider()

st.subheader("Budget Table")

st.dataframe(
    budget_view[
        [
            "category",
            "monthly_limit",
            "spent",
            "remaining",
            "utilization_pct",
            "status",
        ]
    ],
    use_container_width=True,
    hide_index=True
)