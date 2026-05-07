import uuid
from datetime import date, timedelta

import streamlit as st

from lib.auth import require_auth, logout_button
from lib.supabase_client import get_authenticated_supabase_client

st.set_page_config(page_title="Seed Test Data", page_icon="🧪", layout="wide")

st.title("🧪 Seed Test Data")

user_id = require_auth()
logout_button()

supabase = get_authenticated_supabase_client()

st.info(f"Logged in as: {user_id}")

if st.button("Insert test account + transactions"):
    try:
        simplefin_account_id = f"test-checking-{user_id}"

        account_payload = {
            "user_id": user_id,
            "simplefin_account_id": simplefin_account_id,
            "name": "Test Checking Account",
            "type": "checking",
            "balance": 4250.75,
            "currency": "USD",
        }

        account_response = (
            supabase
            .table("accounts")
            .upsert(
                account_payload,
                on_conflict="user_id,simplefin_account_id"
            )
            .execute()
        )

        account_id = account_response.data[0]["id"]

        today = date.today()

        transactions = [
            {
                "user_id": user_id,
                "account_id": account_id,
                "simplefin_transaction_id": f"txn-{user_id}-001",
                "date": str(today - timedelta(days=1)),
                "description": "Walmart Grocery",
                "merchant": "Walmart",
                "amount": -86.42,
                "category": "Groceries",
                "pending": False,
                "raw_data": {"source": "seed"},
            },
            {
                "user_id": user_id,
                "account_id": account_id,
                "simplefin_transaction_id": f"txn-{user_id}-002",
                "date": str(today - timedelta(days=2)),
                "description": "Netflix Subscription",
                "merchant": "Netflix",
                "amount": -15.99,
                "category": "Subscriptions",
                "pending": False,
                "raw_data": {"source": "seed"},
            },
            {
                "user_id": user_id,
                "account_id": account_id,
                "simplefin_transaction_id": f"txn-{user_id}-003",
                "date": str(today - timedelta(days=3)),
                "description": "Shell Fuel",
                "merchant": "Shell",
                "amount": -48.30,
                "category": "Transportation",
                "pending": False,
                "raw_data": {"source": "seed"},
            },
            {
                "user_id": user_id,
                "account_id": account_id,
                "simplefin_transaction_id": f"txn-{user_id}-004",
                "date": str(today - timedelta(days=4)),
                "description": "Payroll Deposit",
                "merchant": "Employer Payroll",
                "amount": 3040.00,
                "category": "Income",
                "pending": False,
                "raw_data": {"source": "seed"},
            },
            {
                "user_id": user_id,
                "account_id": account_id,
                "simplefin_transaction_id": f"txn-{user_id}-005",
                "date": str(today - timedelta(days=5)),
                "description": "Doordash Food Delivery",
                "merchant": "Doordash",
                "amount": -32.75,
                "category": "Dining",
                "pending": False,
                "raw_data": {"source": "seed"},
            },
        ]

        (
            supabase
            .table("transactions")
            .upsert(
                transactions,
                on_conflict="user_id,simplefin_transaction_id"
            )
            .execute()
        )

        st.success("Test account and transactions inserted successfully.")

    except Exception as e:
        st.error(f"Failed to insert test data: {e}")