# def categorize_transaction(description: str, merchant: str = "", user_rules: list[dict] | None = None) -> str:
#     text = f"{description} {merchant}".lower()

#     if user_rules:
#         for rule in user_rules:
#             keyword = str(rule.get("keyword", "")).lower().strip()
#             category = rule.get("category")

#             if keyword and category and keyword in text:
#                 return category

#     rules = {
#         "Groceries": ["walmart", "kroger", "costco", "aldi", "target", "whole foods"],
#         "Dining": ["restaurant", "doordash", "ubereats", "mcdonald", "starbucks", "chipotle"],
#         "Transportation": ["shell", "exxon", "uber", "lyft", "fuel", "gas"],
#         "Subscriptions": ["netflix", "spotify", "hulu", "prime", "openai", "chatgpt"],
#         "Housing": ["rent", "mortgage"],
#         "Utilities": ["electric", "water", "internet", "phone", "utility"],
#         "Healthcare": ["pharmacy", "doctor", "hospital", "cvs", "walgreens"],
#         "Income": ["payroll", "salary", "deposit"],
#     }

#     for category, keywords in rules.items():
#         if any(keyword in text for keyword in keywords):
#             return category

#     return "Uncategorized"

import re
from dataclasses import dataclass

@dataclass
class CategoryResult:
    category: str
    confidence: float
    reason: str

CATEGORIES = [
    "Income",
    "Groceries",
    "Dining",
    "Transportation",
    "Housing",
    "Utilities",
    "Subscriptions",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Education",
    "Travel",
    "Savings",
    "Investments",
    "Debt",
    "Transfers",
    "Fees",
    "Uncategorized",
]

def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value

def contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)

def categorize_transaction_smart(
        description: str,
        merchant: str = "",
        amount: float | None = None,
        user_rules: list[dict] | None = None,
) -> CategoryResult:
    raw_text = f"{merchant} {description}"
    text = normalize_text(raw_text)
    amount_value = float(amount or 0)

    # Apply user-defined rules
    if user_rules:
        for rule in user_rules:
            keyword = normalize_text(str(rule.get("keyword", "")))
            category = rule.get("category")

            if keyword and category and keyword in text:
                return CategoryResult(
                    category=category,
                    confidence=0.98,
                    reason=f"Matched user-learned rule: {keyword}"
                )
            
    # Apply Income detection
    if contains_any(text, [
        r"\bpayroll\b",
        r"\bsalary\b",
        r"\bdirect deposit\b",
        r"\bemployer\b",
        r"\bpaycheck\b",
        r"\bwages\b",
    ]) or amount_value > 0 and contains_any(text, [r"\bdeposit\b"]):
        return CategoryResult("Income", 0.92, "Detected payroll/income pattern")
    
    # Debt / credit cards payments
    if contains_any(text, [
        r"\bamerican express\b",
        r"\bamex\b",
        r"\bdiscover\b",
        r"\bcapital one\b",
        r"\bchase credit\b",
        r"\bciti card\b",
        r"\bcredit card\b",
        r"\bcard payment\b",
        r"\bpayment to\b",
        r"\bautopay\b",
    ]):
        return CategoryResult("Debt", 0.88, "Detected credit card or debt payment pattern")
    
    # 4. Savings / internal savings transfers
    if contains_any(text, [
        r"\bhigh yield\b",
        r"\bhysa\b",
        r"\bsavings account\b",
        r"\btransfer to savings\b",
        r"\bsave\b",
    ]):
        return CategoryResult("Savings", 0.88, "Detected savings transfer pattern")

    # 5. Investments
    if contains_any(text, [
        r"\brobinhood\b",
        r"\bfidelity\b",
        r"\bcharles schwab\b",
        r"\bschwab\b",
        r"\bvanguard\b",
        r"\betrade\b",
        r"\bwebull\b",
        r"\bsecurities\b",
        r"\bstock\b",
        r"\betf\b",
        r"\bbrokerage\b",
        r"\binvest\b",
        r"\btrade\b",
    ]):
        return CategoryResult("Investments", 0.9, "Detected brokerage/investment pattern")

    # 6. Subscriptions
    if contains_any(text, [
        r"\bnetflix\b",
        r"\bspotify\b",
        r"\bhulu\b",
        r"\bdisney\b",
        r"\bdisneyplus\b",
        r"\bprime video\b",
        r"\bapple com bill\b",
        r"\bgoogle youtube\b",
        r"\byoutube premium\b",
        r"\bchatgpt\b",
        r"\bopenai\b",
        r"\bsubscription\b",
        r"\brecurring\b",
    ]):
        return CategoryResult("Subscriptions", 0.93, "Detected recurring subscription merchant")

    # 7. Groceries
    if contains_any(text, [
        r"\bwalmart\b",
        r"\bkroger\b",
        r"\bcostco\b",
        r"\baldi\b",
        r"\bwhole foods\b",
        r"\btrader joe\b",
        r"\bsam s club\b",
        r"\bsuper market\b",
        r"\bsupermarket\b",
        r"\bgrocery\b",
        r"\bfood market\b",
        r"\bmarket\b",
        r"\bmart\b",
    ]):
        return CategoryResult("Groceries", 0.82, "Detected grocery/supermarket pattern")

    # 8. Transportation
    if contains_any(text, [
        r"\bexxon\b",
        r"\bexxonmobil\b",
        r"\bshell\b",
        r"\bbp\b",
        r"\bchevron\b",
        r"\bmarathon\b",
        r"\bmobil\b",
        r"\bfuel\b",
        r"\bgas\b",
        r"\buber ride\b",
        r"\blyft\b",
        r"\bparking\b",
        r"\btoll\b",
    ]):
        return CategoryResult("Transportation", 0.9, "Detected fuel/transportation pattern")

    # 9. Dining
    if contains_any(text, [
        r"\brestaurant\b",
        r"\bdoordash\b",
        r"\buber eats\b",
        r"\bubereats\b",
        r"\bgrubhub\b",
        r"\bstarbucks\b",
        r"\bmcdonald\b",
        r"\bchipotle\b",
        r"\btaco bell\b",
        r"\bsubway\b",
        r"\bpizza\b",
        r"\bcafe\b",
        r"\bcoffee\b",
    ]):
        return CategoryResult("Dining", 0.85, "Detected restaurant/dining pattern")

    # 10. Shopping
    if contains_any(text, [
        r"\bamzn\b",
        r"\bamazon\b",
        r"\btarget\b",
        r"\bbest buy\b",
        r"\bebay\b",
        r"\betcy\b",
        r"\bshop\b",
        r"\bstore\b",
        r"\bretail\b",
    ]):
        return CategoryResult("Shopping", 0.82, "Detected shopping/retail pattern")

    # 11. Utilities
    if contains_any(text, [
        r"\belectric\b",
        r"\bwater\b",
        r"\binternet\b",
        r"\bcomcast\b",
        r"\bxfinity\b",
        r"\bat t\b",
        r"\bverizon\b",
        r"\bt mobile\b",
        r"\butility\b",
        r"\bgas bill\b",
        r"\bMLGW\b",
    ]):
        return CategoryResult("Utilities", 0.86, "Detected utility provider pattern")

    # 12. Housing
    if contains_any(text, [
        r"\brent\b",
        r"\bmortgage\b",
        r"\bapartment\b",
        r"\blease\b",
    ]):
        return CategoryResult("Housing", 0.86, "Detected housing/rent pattern")

    # 13. Healthcare
    if contains_any(text, [
        r"\bcvs\b",
        r"\bwalgreens\b",
        r"\bpharmacy\b",
        r"\bdoctor\b",
        r"\bhospital\b",
        r"\bmedical\b",
        r"\bdental\b",
    ]):
        return CategoryResult("Healthcare", 0.84, "Detected healthcare/pharmacy pattern")

    # 14. Transfers
    if contains_any(text, [
        r"\bzelle\b",
        r"\bvenmo\b",
        r"\bcash app\b",
        r"\btransfer\b",
        r"\bach\b",
        r"\bwire\b",
    ]):
        return CategoryResult("Transfers", 0.65, "Detected generic transfer pattern; needs review")

    # 15. Fees
    if contains_any(text, [
        r"\bfee\b",
        r"\bmaintenance charge\b",
        r"\boverdraft\b",
        r"\batm fee\b",
    ]):
        return CategoryResult("Fees", 0.86, "Detected banking fee pattern")

    return CategoryResult(
        category="Uncategorized",
        confidence=0.0,
        reason="No confident category pattern matched"
    )

    def categorize_transaction(
            description: str,
            merchant: str = "",
            user_rules: list[dict] | None = None,
    ) -> str:
        result = categorize_transaction_smart(
            description=description,
            merchant=merchant,
            user_rules=user_rules          
        )
        return result.category