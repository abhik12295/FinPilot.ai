# import os
# import json
# from typing import Any

# import pandas as pd
# from dotenv import load_dotenv
# from openai import OpenAI

# load_dotenv()


# def get_openai_client() -> OpenAI:
#     api_key = os.getenv("OPENAI_API_KEY")

#     if not api_key:
#         raise ValueError("Missing OPENAI_API_KEY in .env")

#     return OpenAI(api_key=api_key)


# def build_finance_context(
#     accounts_df: pd.DataFrame,
#     transactions_df: pd.DataFrame,
#     budgets_df: pd.DataFrame | None = None,
#     subscriptions_df: pd.DataFrame | None = None,
# ) -> dict[str, Any]:
#     tx = transactions_df.copy()

#     if tx.empty:
#         return {
#             "accounts": [],
#             "summary": "No transactions available.",
#             "transactions": [],
#             "budgets": [],
#             "subscriptions": [],
#         }

#     tx["date"] = pd.to_datetime(tx["date"])
#     tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0)

#     current_month = pd.Timestamp.today().month
#     current_year = pd.Timestamp.today().year

#     monthly_tx = tx[
#         (tx["date"].dt.month == current_month)
#         & (tx["date"].dt.year == current_year)
#     ].copy()

#     spending_tx = monthly_tx[monthly_tx["amount"] < 0].copy()
#     spending_tx["spend"] = spending_tx["amount"].abs()

#     income = monthly_tx[monthly_tx["amount"] > 0]["amount"].sum()
#     spending = spending_tx["spend"].sum()
#     net_cash_flow = income - spending

#     category_summary = (
#         spending_tx.groupby("category")["spend"]
#         .sum()
#         .sort_values(ascending=False)
#         .to_dict()
#         if not spending_tx.empty
#         else {}
#     )

#     recent_transactions = (
#         tx.sort_values("date", ascending=False)
#         .head(25)[["date", "merchant", "description", "amount", "category"]]
#         .assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d"))
#         .to_dict(orient="records")
#     )

#     accounts = (
#         accounts_df[["name", "type", "balance", "currency"]]
#         .to_dict(orient="records")
#         if not accounts_df.empty
#         else []
#     )

#     budgets = (
#         budgets_df[["category", "monthly_limit"]].to_dict(orient="records")
#         if budgets_df is not None and not budgets_df.empty
#         else []
#     )

#     subscriptions = (
#         subscriptions_df[["merchant", "amount", "frequency", "status"]].to_dict(orient="records")
#         if subscriptions_df is not None and not subscriptions_df.empty
#         else []
#     )

#     return {
#         "accounts": accounts,
#         "monthly_summary": {
#             "income": round(float(income), 2),
#             "spending": round(float(spending), 2),
#             "net_cash_flow": round(float(net_cash_flow), 2),
#             "category_spending": category_summary,
#         },
#         "recent_transactions": recent_transactions,
#         "budgets": budgets,
#         "subscriptions": subscriptions,
#     }


# def ask_finpilot_ai(
#     question: str,
#     accounts_df: pd.DataFrame,
#     transactions_df: pd.DataFrame,
#     budgets_df: pd.DataFrame | None = None,
#     subscriptions_df: pd.DataFrame | None = None,
# ) -> str:
#     client = get_openai_client()
#     model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

#     finance_context = build_finance_context(
#         accounts_df=accounts_df,
#         transactions_df=transactions_df,
#         budgets_df=budgets_df,
#         subscriptions_df=subscriptions_df,
#     )

#     system_prompt = """
# You are FinPilot AI, a personal finance planning assistant.

# Rules:
# - Use only the provided finance context.
# - Do not invent transactions, balances, bills, or income.
# - Be specific and practical.
# - Explain reasoning clearly.
# - If data is insufficient, say what is missing.
# - Do not provide legal, tax, or investment advice.
# - Keep the answer concise but useful.
# """

#     user_prompt = f"""
# User question:
# {question}

# Finance context JSON:
# {json.dumps(finance_context, indent=2)}
# """

#     response = client.responses.create(
#         model=model,
#         input=[
#             {
#                 "role": "system",
#                 "content": system_prompt,
#             },
#             {
#                 "role": "user",
#                 "content": user_prompt,
#             },
#         ],
#     )

#     return response.output_text


# using ollama local

import os
import json
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv
import re

load_dotenv()


def build_finance_context(
    accounts_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    budgets_df: pd.DataFrame | None = None,
    subscriptions_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    tx = transactions_df.copy()

    if tx.empty:
        return {
            "accounts": [],
            "summary": "No transactions available.",
            "recent_transactions": [],
            "budgets": [],
            "subscriptions": [],
        }

    tx["date"] = pd.to_datetime(tx["date"])
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0)

    # current_month = pd.Timestamp.today().month
    # current_year = pd.Timestamp.today().year

    # monthly_tx = tx[
    #     (tx["date"].dt.month == current_month)
    #     & (tx["date"].dt.year == current_year)
    # ].copy()

    monthly_tx = tx.copy()

    spending_tx = monthly_tx[monthly_tx["amount"] < 0].copy()
    spending_tx["spend"] = spending_tx["amount"].abs()

    income = monthly_tx[monthly_tx["amount"] > 0]["amount"].sum()
    spending = spending_tx["spend"].sum()
    net_cash_flow = income - spending

    category_summary = (
        spending_tx.groupby("category")["spend"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
        if not spending_tx.empty
        else {}
    )

    recent_transactions = (
        tx.sort_values("date", ascending=False)
        .head(25)[["date", "merchant", "description", "amount", "category"]]
        .assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d"))
        .to_dict(orient="records")
    )

    accounts = (
        accounts_df[["name", "type", "balance", "currency"]]
        .to_dict(orient="records")
        if not accounts_df.empty
        else []
    )

    budgets = (
        budgets_df[["category", "monthly_limit"]].to_dict(orient="records")
        if budgets_df is not None and not budgets_df.empty
        else []
    )

    subscriptions = (
        subscriptions_df[["merchant", "amount", "frequency", "status"]].to_dict(orient="records")
        if subscriptions_df is not None and not subscriptions_df.empty
        else []
    )

    return {
        "accounts": accounts,
        "monthly_summary": {
            "income": round(float(income), 2),
            "spending": round(float(spending), 2),
            "net_cash_flow": round(float(net_cash_flow), 2),
            "category_spending": category_summary,
        },
        "recent_transactions": recent_transactions,
        "budgets": budgets,
        "subscriptions": subscriptions,
    }

def extract_purchase_amount(question:str) -> float | None:
    matches = re.findall(r"\$?\s?(\d+(?:\.\d{1,2})?)", question)
    if matches:
        return float(matches[0])
    return None

def ask_finpilot_ai(
    question: str,
    accounts_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    budgets_df: pd.DataFrame | None = None,
    subscriptions_df: pd.DataFrame | None = None,
) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")

    finance_context = build_finance_context(
        accounts_df=accounts_df,
        transactions_df=transactions_df,
        budgets_df=budgets_df,
        subscriptions_df=subscriptions_df,
    )

    summary = finance_context.get("monthly_summary", {})
    income = summary.get("income", 0)
    spending = summary.get("spending", 0)
    net_cash_flow = summary.get("net_cash_flow", 0)

    total_balance = 0
    for account in finance_context.get("accounts", []):
        total_balance += float(account.get("balance", 0))

    safe_purchase_limit = max(0, net_cash_flow * 0.5)
    purchase_amount = max(0, net_cash_flow * 0.5)
    if purchase_amount is not None:
        can_afford = purchase_amount <= safe_purchase_limit
    else:
        can_afford = None

    computed_metrics = {
        "total_balance": round(total_balance, 2),
        "monthly_income": income,
        "monthly_spending": spending,
        "net_cash_flow": net_cash_flow,
        "estimated_safe_purchase_limit": round(safe_purchase_limit, 2),
        "requested_purchase_amount": purchase_amount,
        "can_afford_requested_purchase": can_afford
    }

    system_prompt = """
        You are FinPilot AI, a personal finance assistant.

        Critical rules:
        - Use computed_metrics as the ONLY source of truth.
        - NEVER use total_balance to decide affordability.
        - Affordability MUST be based on:
            → net_cash_flow
            → estimated_safe_purchase_limit

        - If can_afford_requested_purchase is true:
            → say it is affordable based on cash flow

        - If false:
            → say it is not safe

        - Do NOT justify affordability using balance alone.

        Formatting rules:
        - Use clean Markdown
        - Use ### sections
        - Use bullet points
        - Format money like $1,234.56
        - No repetition
        - No merged words
        - Do not repeat sentences.
        - Keep sentences clear, human readable.
        - Keep text clear and professional, no jargon or slang.

        Safety rules:
        - Do not invent numbers
        - Do not contradict computed_metrics
        - If data is limited, say that
        """
    
    user_prompt = f"""
        User question:
        {question}

        Computed metrics:
        {json.dumps(computed_metrics, indent=2)}

        Finance context:
        {json.dumps(finance_context, indent=2)}

        Answer in clean Markdown:
        """

    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": system_prompt + "\n\n" + user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 4096,
                "repeat_penalty": 1.25
            }
        },
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(f"Ollama error: {response.text}")

    return response.json().get("response", "").strip()