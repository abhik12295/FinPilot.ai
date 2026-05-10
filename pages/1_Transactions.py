import keyword

import pandas as pd
import streamlit as st

from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client

st.set_page_config(
    page_title="Transactions | FinPilot AI",
    page_icon="💳",
    layout="wide"
)

st.title("💳 Transactions")
st.caption("Search, filter, and manage your transaction categories.")

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


def update_transaction_category(transaction_id: str, new_category: str):
    return (
        supabase
        .table("transactions")
        .update({"category": new_category})
        .eq("id", transaction_id)
        .eq("user_id", user_id)
        .execute()
    )

def save_category_rule(keyword:str, category:str):
    payload = {
        "user_id": user_id,
        "keyword": keyword.lower().strip(),
        "category": category
    }
    return supabase.table("category_rules").upsert(payload, on_conflict="user_id,keyword").execute()


transactions_df = load_transactions(user_id)

if transactions_df.empty:
    st.info("No transactions found yet.")
    st.stop()

transactions_df["date"] = pd.to_datetime(transactions_df["date"])
transactions_df["amount"] = pd.to_numeric(transactions_df["amount"], errors="coerce").fillna(0)

st.subheader("Filters")

col1, col2, col3 = st.columns(3)

with col1:
    min_date = transactions_df["date"].min().date()
    max_date = transactions_df["date"].max().date()

    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

with col2:
    selected_categories = st.multiselect(
        "Category",
        options=sorted(transactions_df["category"].dropna().unique()),
        default=sorted(transactions_df["category"].dropna().unique())
    )

with col3:
    search_text = st.text_input("Search merchant or description")

filtered_df = transactions_df.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["date"].dt.date >= start_date)
        & (filtered_df["date"].dt.date <= end_date)
    ]

if selected_categories:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]

if search_text:
    search_lower = search_text.lower()
    filtered_df = filtered_df[
        filtered_df["merchant"].fillna("").str.lower().str.contains(search_lower)
        | filtered_df["description"].fillna("").str.lower().str.contains(search_lower)
    ]

st.divider()

total_income = filtered_df[filtered_df["amount"] > 0]["amount"].sum()
total_spending = filtered_df[filtered_df["amount"] < 0]["amount"].abs().sum()
net = total_income - total_spending

m1, m2, m3, m4 = st.columns(4)

m1.metric("Filtered Transactions", len(filtered_df))
m2.metric("Income", f"${total_income:,.2f}")
m3.metric("Spending", f"${total_spending:,.2f}")
m4.metric("Net", f"${net:,.2f}")

st.divider()

st.subheader("Transaction List")

if filtered_df.empty:
    st.warning("No transactions match your filters.")
    st.stop()

display_df = filtered_df[
    [
        "date",
        "merchant",
        "description",
        "amount",
        "category",
        "pending",
        "id",
    ]
].copy()

display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

st.dataframe(
    display_df.drop(columns=["id"]),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("Edit Category")

transaction_options = {
    f"{row['date']} | {row['merchant']} | ${row['amount']:,.2f} | {row['category']}": row["id"]
    for _, row in display_df.iterrows()
}

selected_transaction_label = st.selectbox(
    "Select transaction",
    options=list(transaction_options.keys())
)

selected_transaction_id = transaction_options[selected_transaction_label]

current_category = display_df.loc[
    display_df["id"] == selected_transaction_id,
    "category"].iloc[0]

new_category = st.selectbox(
    "New category",
    options=CATEGORIES,
    index=CATEGORIES.index(current_category) if current_category in CATEGORIES else CATEGORIES.index("Uncategorized")
)

learn_rule = st.checkbox("Remember this merchant/category rule for future uploads")
if st.button("Update Category"):
    try:
        update_transaction_category(selected_transaction_id, new_category)
        if learn_rule:
            selected_row =  display_df[display_df["id"] == selected_transaction_id]
            keyword = selected_row["merchant"]

            if keyword:
                save_category_rule(keyword, new_category)
            
            st.cache_data.clear()
            st.success("Category updated successfully.")
            st.rerun()
    
    except Exception as e:
        st.error(f"Failed to update category: {e}")
        

    