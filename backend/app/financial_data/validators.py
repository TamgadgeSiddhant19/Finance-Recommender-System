from decimal import Decimal
from typing import List, Optional, Tuple
from app.financial_data.schemas import (
    FinancialProductBase,
    MarketDataBase,
)


class DataValidationError(Exception):
    """Raised when record fails financial domain integrity checks."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or [message]


def validate_product_data(product: FinancialProductBase) -> Tuple[bool, List[str]]:
    """
    Validate domain integrity rules for financial product records.
    """
    errors: List[str] = []

    if not product.symbol or not product.symbol.strip():
        errors.append("Product symbol cannot be empty.")
    elif len(product.symbol.strip()) > 50:
        errors.append("Product symbol cannot exceed 50 characters.")

    if not product.name or not product.name.strip():
        errors.append("Product name cannot be empty.")

    if product.minimum_investment < Decimal("0.00"):
        errors.append(f"Minimum investment must be non-negative, got {product.minimum_investment}.")

    if product.expense_ratio is not None:
        if product.expense_ratio < Decimal("0.0000") or product.expense_ratio > Decimal("1.0000"):
            errors.append(f"Expense ratio must be between 0.0 and 1.0 (fraction), got {product.expense_ratio}.")

    if not product.currency or len(product.currency.strip()) > 10:
        errors.append("Currency code must be non-empty and under 10 characters.")

    return len(errors) == 0, errors


def validate_market_data(record: MarketDataBase) -> Tuple[bool, List[str]]:
    """
    Validate OHLCV market pricing invariants:
    - Prices must be non-negative
    - High price must be >= Low price
    - High must be >= Open and Close
    - Low must be <= Open and Close
    - Volume must be >= 0
    """
    errors: List[str] = []

    if record.open_price < Decimal("0.00"):
        errors.append(f"Open price cannot be negative: {record.open_price}")
    if record.high_price < Decimal("0.00"):
        errors.append(f"High price cannot be negative: {record.high_price}")
    if record.low_price < Decimal("0.00"):
        errors.append(f"Low price cannot be negative: {record.low_price}")
    if record.close_price < Decimal("0.00"):
        errors.append(f"Close price cannot be negative: {record.close_price}")
    if record.volume < 0:
        errors.append(f"Volume cannot be negative: {record.volume}")

    # OHLC Consistency
    if record.high_price < record.low_price:
        errors.append(f"High price ({record.high_price}) cannot be lower than low price ({record.low_price}).")
    if record.high_price < record.open_price:
        errors.append(f"High price ({record.high_price}) cannot be lower than open price ({record.open_price}).")
    if record.high_price < record.close_price:
        errors.append(f"High price ({record.high_price}) cannot be lower than close price ({record.close_price}).")
    if record.low_price > record.open_price:
        errors.append(f"Low price ({record.low_price}) cannot be greater than open price ({record.open_price}).")
    if record.low_price > record.close_price:
        errors.append(f"Low price ({record.low_price}) cannot be greater than close price ({record.close_price}).")

    return len(errors) == 0, errors
