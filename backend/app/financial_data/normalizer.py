from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductCreate,
    MarketDataCreate,
    ProductRiskLevel,
    ProductType,
)


def quantize_decimal(val: Any, places: int = 2) -> Decimal:
    """Helper to convert any input into a Decimal quantized to specific places."""
    if val is None or val == "":
        return Decimal("0.00")
    if not isinstance(val, Decimal):
        d_val = Decimal(str(val).strip())
    else:
        d_val = val
    pattern = Decimal("10") ** -places
    return d_val.quantize(pattern, rounding=ROUND_HALF_UP)


def normalize_product_dict(raw: Dict[str, Any]) -> FinancialProductCreate:
    """
    Normalize raw string/dict data into a strongly-typed FinancialProductCreate instance.
    """
    symbol = str(raw.get("symbol", "")).strip().upper()
    name = str(raw.get("name", "")).strip()
    product_type_str = str(raw.get("product_type", "")).strip().lower()
    asset_class_str = str(raw.get("asset_class", "")).strip().lower()
    issuer = str(raw.get("issuer", "")).strip()
    currency = str(raw.get("currency", "INR")).strip().upper()
    country = str(raw.get("country", "India")).strip()
    risk_level_str = str(raw.get("risk_level", "")).strip().lower()

    # Expense ratio
    raw_expense = raw.get("expense_ratio")
    if raw_expense is not None and str(raw_expense).strip() != "":
        expense_ratio = quantize_decimal(raw_expense, 4)
    else:
        expense_ratio = None

    # Minimum investment
    raw_min_inv = raw.get("minimum_investment", "500.00")
    minimum_investment = quantize_decimal(raw_min_inv, 2)

    return FinancialProductCreate(
        symbol=symbol,
        name=name,
        product_type=ProductType(product_type_str),
        asset_class=AssetClass(asset_class_str),
        issuer=issuer,
        currency=currency,
        country=country,
        risk_level=ProductRiskLevel(risk_level_str),
        expense_ratio=expense_ratio,
        minimum_investment=minimum_investment,
    )


def normalize_market_data_dict(raw: Dict[str, Any]) -> MarketDataCreate:
    """
    Normalize raw dict market pricing data into MarketDataCreate.
    """
    symbol = str(raw.get("symbol", "")).strip().upper() if "symbol" in raw else None
    product_id = int(raw["financial_product_id"]) if "financial_product_id" in raw and raw["financial_product_id"] else None

    # Parse timestamp
    raw_ts = raw.get("timestamp")
    if isinstance(raw_ts, datetime):
        ts = raw_ts if raw_ts.tzinfo else raw_ts.replace(tzinfo=timezone.utc)
    else:
        ts = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
        if not ts.tzinfo:
            ts = ts.replace(tzinfo=timezone.utc)

    open_p = quantize_decimal(raw.get("open_price", "0.00"), 2)
    high_p = quantize_decimal(raw.get("high_price", "0.00"), 2)
    low_p = quantize_decimal(raw.get("low_price", "0.00"), 2)
    close_p = quantize_decimal(raw.get("close_price", "0.00"), 2)
    vol = int(raw.get("volume", 0))
    source = str(raw.get("source", "demo/synthetic")).strip()

    return MarketDataCreate(
        symbol=symbol,
        financial_product_id=product_id,
        timestamp=ts,
        open_price=open_p,
        high_price=high_p,
        low_price=low_p,
        close_price=close_p,
        volume=vol,
        source=source,
    )
