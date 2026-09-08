from decimal import Decimal
from typing import List, Sequence, Tuple, Union
from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import FinancialProductResponse
from app.recommendations.constants import ALLOWED_PRODUCT_RISK_MAP

ProductTypeUnion = Union[FinancialProduct, FinancialProductResponse]


def filter_eligible_products(
    products: Sequence[ProductTypeUnion],
    risk_category: str,
    investment_capacity: Decimal,
) -> Tuple[List[ProductTypeUnion], List[dict]]:
    """
    Deterministically filters financial products against user risk profile,
    investment capacity limits, and ecosystem constraints.

    Returns:
        (eligible_products, exclusion_logs)
    """
    category_key = risk_category.upper()
    allowed_risks = ALLOWED_PRODUCT_RISK_MAP.get(
        category_key,
        {"low", "moderate"},  # Safe conservative fallback
    )

    eligible: List[ProductTypeUnion] = []
    exclusions: List[dict] = []

    for product in products:
        risk_str = (
            product.risk_level.value
            if hasattr(product.risk_level, "value")
            else str(product.risk_level).lower()
        )
        min_invest = Decimal(str(product.minimum_investment))

        # 1. Check Risk Eligibility
        if risk_str not in allowed_risks:
            exclusions.append({
                "symbol": product.symbol,
                "name": product.name,
                "reason": (
                    f"Product risk level '{risk_str}' exceeds allowed risk levels "
                    f"{list(allowed_risks)} for '{risk_category}' risk profile."
                ),
            })
            continue

        # 2. Check Minimum Investment vs Capacity
        if investment_capacity > Decimal("0.00") and min_invest > investment_capacity:
            exclusions.append({
                "symbol": product.symbol,
                "name": product.name,
                "reason": (
                    f"Minimum investment requirement (₹{min_invest}) exceeds "
                    f"available user capacity (₹{investment_capacity})."
                ),
            })
            continue

        # 3. Currency / Market Validation
        if getattr(product, "currency", "INR") != "INR":
            exclusions.append({
                "symbol": product.symbol,
                "name": product.name,
                "reason": f"Product currency '{product.currency}' is not supported (Expected INR).",
            })
            continue

        eligible.append(product)

    return eligible, exclusions
