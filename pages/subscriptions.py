import pandas as pd
import streamlit as st

from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client

st.set_page_config(
    page_title="Subscriptions | FinPilot AI",
    page_icon="🔁",
    layout="wide"
)

st.title("🔁 Subscriptions")
st.caption("Detect recurring merchants and track possible subscription charges.")

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
def load_subscriptions(current_user_id: str) -> pd.DataFrame:
    response = (
        supabase
        .table("subscriptions")
        .select("*")
        .eq("user_id", current_user_id)
        .order("last_seen", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)


def upsert_subscription(row):
    payload = {
        "user_id": user_id,
        "merchant": row["merchant"],
        "amount": float(row["avg_amount"]),
        "frequency": row["frequency"],
        "last_seen": str(row["last_seen"].date()),
        "status": "active",
    }

    return (
        supabase
        .table("subscriptions")
        .upsert(payload, on_conflict="user_id,merchant")
        .execute()
    )


transactions_df = load_transactions(user_id)

if transactions_df.empty:
    st.info("No transactions found yet.")
    st.stop()

transactions_df["date"] = pd.to_datetime(transactions_df["date"])
transactions_df["amount"] = pd.to_numeric(transactions_df["amount"], errors="coerce").fillna(0)

spending_df = transactions_df[transactions_df["amount"] < 0].copy()
spending_df["charge_amount"] = spending_df["amount"].abs()

st.subheader("Detected Recurring Merchants")

merchant_summary = (
    spending_df
    .groupby("merchant")
    .agg(
        transaction_count=("id", "count"),
        avg_amount=("charge_amount", "mean"),
        min_amount=("charge_amount", "min"),
        max_amount=("charge_amount", "max"),
        first_seen=("date", "min"),
        last_seen=("date", "max"),
    )
    .reset_index()
)

merchant_summary["days_active"] = (
    merchant_summary["last_seen"] - merchant_summary["first_seen"]
).dt.days

detected_df = merchant_summary[
    (merchant_summary["transaction_count"] >= 2)
    | (
        merchant_summary["merchant"]
        .str.lower()
        .str.contains("netflix|spotify|hulu|prime|apple|google|openai|chatgpt|gym|insurance|subscription")
    )
].copy()

if detected_df.empty:
    st.info("No recurring subscriptions detected yet. Add more transactions and try again.")
else:
    detected_df["frequency"] = "monthly"
    detected_df["avg_amount"] = detected_df["avg_amount"].round(2)

    c1, c2, c3 = st.columns(3)
    c1.metric("Detected", len(detected_df))
    c2.metric("Estimated Monthly Cost", f"${detected_df['avg_amount'].sum():,.2f}")
    c3.metric("Highest Subscription", f"${detected_df['avg_amount'].max():,.2f}")

    st.dataframe(
        detected_df[
            [
                "merchant",
                "transaction_count",
                "avg_amount",
                "min_amount",
                "max_amount",
                "first_seen",
                "last_seen",
                "frequency",
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    if st.button("Save Detected Subscriptions"):
        try:
            for _, row in detected_df.iterrows():
                upsert_subscription(row)

            st.cache_data.clear()
            st.success("Detected subscriptions saved successfully.")
            st.rerun()

        except Exception as e:
            st.error(f"Failed to save subscriptions: {e}")

st.divider()

st.subheader("Saved Subscriptions")

subscriptions_df = load_subscriptions(user_id)

if subscriptions_df.empty:
    st.info("No saved subscriptions yet.")
else:
    active_df = subscriptions_df[subscriptions_df["status"] == "active"].copy()
    active_df["amount"] = pd.to_numeric(active_df["amount"], errors="coerce").fillna(0)

    m1, m2 = st.columns(2)
    m1.metric("Active Subscriptions", len(active_df))
    m2.metric("Monthly Subscription Cost", f"${active_df['amount'].sum():,.2f}")

    st.dataframe(
        subscriptions_df[
            [
                "merchant",
                "amount",
                "frequency",
                "last_seen",
                "status",
                "created_at",
            ]
        ],
        use_container_width=True,
        hide_index=True
    )