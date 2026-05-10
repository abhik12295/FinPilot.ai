def categorize_transaction(description: str, merchant: str = "", user_rules: list[dict] | None = None) -> str:
    text = f"{description} {merchant}".lower()

    if user_rules:
        for rule in user_rules:
            keyword = str(rule.get("keyword", "")).lower().strip()
            category = rule.get("category")

            if keyword and category and keyword in text:
                return category

    rules = {
        "Groceries": ["walmart", "kroger", "costco", "aldi", "target", "whole foods"],
        "Dining": ["restaurant", "doordash", "ubereats", "mcdonald", "starbucks", "chipotle"],
        "Transportation": ["shell", "exxon", "uber", "lyft", "fuel", "gas"],
        "Subscriptions": ["netflix", "spotify", "hulu", "prime", "openai", "chatgpt"],
        "Housing": ["rent", "mortgage"],
        "Utilities": ["electric", "water", "internet", "phone", "utility"],
        "Healthcare": ["pharmacy", "doctor", "hospital", "cvs", "walgreens"],
        "Income": ["payroll", "salary", "deposit"],
    }

    for category, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "Uncategorized"