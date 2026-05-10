import hashlib
from datetime import datetime
from httpx import get
import pandas as pd
import streamlit as st
from lib.auth import require_auth, logout_button
from lib.categorizer import categorize_transaction
from lib.supabase_client import get_authenticated_supabase_client

st.set_page_config(
    page_title="Upload Transactions | FinPilot AI",
    page_icon="💰",
    layout="wide"
)

st.title("Upload Transactions")
st.caption("Upload a csv file, validate transactions, auto-categorize, and save to supabase.")

# get user_id
user_id = require_auth()
logout_button()

#get authenticated supabase client
supabase = get_authenticated_supabase_client()
REQUIRED_COLUMNS = ["date", "description", "amount"]

@st.cache_data(ttl=60)
def load_accounts(current_user_id: str):
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
def load_category_rules(current_user_id: str) -> list[dict]:
    response = (
        supabase
        .table("category_rules")
        .select("*")
        .eq("user_id", current_user_id)
        .execute()
    )
    return response.data

def make_transaction_id(row:pd.Series) -> str:
    raw = f"{user_id}|{row['date']}|{row['description']}|{row['amount']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def normalize_csv(df:pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [
        col.strip().lower().replace(" ","_")
        for col in df.columns
    ]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns : {missing}")
    
    if "merchant" not in df.columns:
        df["merchant"] = df["description"]
    
    if "category" not in df.columns:
        df["category"] = None

    if "pending" not in df.columns:
        df["pending"] = False
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount", "description"])

    df['description'] = df['description'].astype(str).str.strip()
    df['merchant'] = df['merchant'].fillna(df['description']).astype(str).str.strip()

    df['category'] = df.apply(
        lambda row: row['category']
        if pd.notna(row['category']) and str(row['category']).strip()
        else categorize_transaction(row['description'], row['merchant'], category_rules),
        axis=1
    )

    df['pending'] = df['pending'].astype(bool)
    return df

def insert_transactions(df: pd.DataFrame, account_id: str):
    payload = []

    for _, row in df.iterrows():
        simplefin_transaction_id = make_transaction_id(row)

        payload.append({
            "user_id": user_id,
            "account_id": account_id,
            "simplefin_transaction_id": simplefin_transaction_id,
            "date": str(row["date"]),
            "description": row["description"],
            "merchant": row["merchant"],
            "amount": float(row["amount"]),
            "category": row["category"],
            "pending": bool(row["pending"]),
            "raw_data": {
                "source": "csv_upload",
                "uploaded_at": datetime.utcnow().isoformat()
            }
        })

    return (
        supabase
        .table("transactions")
        .upsert(payload, on_conflict="user_id,simplefin_transaction_id")
        .execute()
    )


accounts_df = load_accounts(user_id)
category_rules = load_category_rules(user_id)

if accounts_df.empty:
    st.warning("No accounts found. Create or seed an account first.")
    st.stop()

account_options = {
    f"{row['name']} ({row['type']}) - ${row['balance']:,.2f}": row["id"]
    for _, row in accounts_df.iterrows()
}

selected_account_label = st.selectbox(
    "Select account for uploaded transactions",
    options=list(account_options.keys())
)

selected_account_id = account_options[selected_account_label]

uploaded_file = st.file_uploader(
    "Upload CSV",
    type=["csv"]
)

st.info(
    "Required columns: date, description, amount. "
    "Optional columns: merchant, category, pending."
)

if uploaded_file:
    try:
        raw_df = pd.read_csv(uploaded_file)
        normalized_df = normalize_csv(raw_df)

        st.subheader("Preview")
        st.dataframe(
            normalized_df[["date", "merchant", "description", "amount", "category", "pending"]],
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Rows Ready", len(normalized_df))
        c2.metric("Total Income", f"${normalized_df[normalized_df['amount'] > 0]['amount'].sum():,.2f}")
        c3.metric("Total Spending", f"${normalized_df[normalized_df['amount'] < 0]['amount'].abs().sum():,.2f}")

        if st.button("Save Transactions to Supabase"):
            if normalized_df.empty:
                st.warning("No valid transactions to save.")
            else:
                insert_transactions(normalized_df, selected_account_id)
                st.cache_data.clear()
                st.success("Transactions uploaded successfully.")

    except Exception as e:
        st.error(f"Upload failed: {e}")