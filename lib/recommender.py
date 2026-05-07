import pandas as pd


def generate_recommendations(
    transactions_df: pd.DataFrame,
    budgets_df: pd.DataFrame | None = None
):
    recommendations = []

    if transactions_df.empty:
        return recommendations

    df = transactions_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    current_month = pd.Timestamp.today().month
    current_year = pd.Timestamp.today().year

    monthly_df = df[
        (df["date"].dt.month == current_month)
        & (df["date"].dt.year == current_year)
    ].copy()

    spending_df = monthly_df[monthly_df["amount"] < 0].copy()
    spending_df["spend"] = spending_df["amount"].abs()

    # =========================
    # 1. Budget-aware overspending
    # =========================
    if budgets_df is not None and not budgets_df.empty and not spending_df.empty:
        budgets = budgets_df.copy()
        budgets["monthly_limit"] = pd.to_numeric(
            budgets["monthly_limit"],
            errors="coerce"
        ).fillna(0)

        category_spend = (
            spending_df
            .groupby("category", as_index=False)["spend"]
            .sum()
        )

        budget_view = budgets.merge(
            category_spend,
            on="category",
            how="left"
        )

        budget_view["spend"] = budget_view["spend"].fillna(0)
        budget_view["utilization_pct"] = (
            budget_view["spend"] / budget_view["monthly_limit"] * 100
        ).round(2)

        for _, row in budget_view.iterrows():
            category = row["category"]
            spend = row["spend"]
            limit = row["monthly_limit"]
            utilization = row["utilization_pct"]

            if limit <= 0:
                continue

            if spend > limit:
                recommendations.append({
                    "type": "budget",
                    "title": f"{category} is over budget",
                    "message": (
                        f"You spent ${spend:,.2f} on {category}, "
                        f"which is above your ${limit:,.2f} monthly budget "
                        f"({utilization:.1f}% used)."
                    ),
                    "priority": "high"
                })

            elif utilization >= 80:
                recommendations.append({
                    "type": "budget",
                    "title": f"{category} is close to budget limit",
                    "message": (
                        f"You have used {utilization:.1f}% of your {category} budget. "
                        f"Spent ${spend:,.2f} out of ${limit:,.2f}."
                    ),
                    "priority": "medium"
                })

    # =========================
    # 2. Top spending category
    # =========================
    if not spending_df.empty:
        category_spend = (
            spending_df
            .groupby("category")["spend"]
            .sum()
            .sort_values(ascending=False)
        )

        top_category = category_spend.index[0]
        top_value = category_spend.iloc[0]

        recommendations.append({
            "type": "spending_summary",
            "title": f"Top spending category: {top_category}",
            "message": (
                f"Your highest spending category this month is {top_category} "
                f"at ${top_value:,.2f}."
            ),
            "priority": "low"
        })

    # =========================
    # 3. Subscription detection
    # =========================
    merchant_counts = df[df["amount"] < 0]["merchant"].value_counts()
    recurring_merchants = merchant_counts[merchant_counts >= 2]

    for merchant in recurring_merchants.index:
        recommendations.append({
            "type": "subscription",
            "title": "Recurring payment detected",
            "message": f"{merchant} appears multiple times and may be a subscription.",
            "priority": "medium"
        })

    # =========================
    # 4. Unusual transaction detection
    # =========================
    if not spending_df.empty:
        avg_spend = spending_df["spend"].mean()
        unusual = spending_df[spending_df["spend"] > avg_spend * 2]

        for _, row in unusual.iterrows():
            recommendations.append({
                "type": "anomaly",
                "title": "Unusual high transaction",
                "message": (
                    f"{row['merchant']} transaction of ${row['spend']:,.2f} "
                    f"is more than 2x your average spending transaction."
                ),
                "priority": "high"
            })

    # =========================
    # 5. Savings rate check
    # =========================
    total_income = monthly_df[monthly_df["amount"] > 0]["amount"].sum()
    total_spending = spending_df["spend"].sum()

    if total_income > 0:
        savings_rate = (total_income - total_spending) / total_income

        if savings_rate < 0.2:
            recommendations.append({
                "type": "savings",
                "title": "Low savings rate",
                "message": (
                    f"Your estimated savings rate this month is "
                    f"{savings_rate * 100:.1f}%. Aim for at least 20%."
                ),
                "priority": "high"
            })

    return recommendations