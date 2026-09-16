from decimal import Decimal
from typing import Dict

# ------------------------------------------------------------------------------
# 1. Scoring Weights (Configurable & Centralized)
# ------------------------------------------------------------------------------
# Sum of weights = 1.00
WEIGHT_RISK_FIT: Decimal = Decimal("0.25")
WEIGHT_HORIZON_FIT: Decimal = Decimal("0.20")
WEIGHT_ASSET_CLASS_FIT: Decimal = Decimal("0.20")
WEIGHT_GOAL_FIT: Decimal = Decimal("0.10")
WEIGHT_COST_EFFICIENCY: Decimal = Decimal("0.10")
WEIGHT_CAPACITY_COMPATIBILITY: Decimal = Decimal("0.05")
WEIGHT_MARKET_PERFORMANCE: Decimal = Decimal("0.05")
WEIGHT_DATA_QUALITY: Decimal = Decimal("0.05")

# ------------------------------------------------------------------------------
# 2. Base Asset Allocation Matrices by Risk Category
# ------------------------------------------------------------------------------
# Target percentages for Equity, Debt, Gold, Cash/Liquid
BASE_ALLOCATION_MATRIX: Dict[str, Dict[str, Decimal]] = {
    "CONSERVATIVE": {
        "equity": Decimal("25.00"),
        "debt": Decimal("65.00"),
        "gold": Decimal("5.00"),
        "cash": Decimal("5.00"),
    },
    "MODERATE": {
        "equity": Decimal("55.00"),
        "debt": Decimal("35.00"),
        "gold": Decimal("10.00"),
        "cash": Decimal("0.00"),
    },
    "AGGRESSIVE": {
        "equity": Decimal("75.00"),
        "debt": Decimal("15.00"),
        "gold": Decimal("10.00"),
        "cash": Decimal("0.00"),
    },
    "VERY_AGGRESSIVE": {
        "equity": Decimal("85.00"),
        "debt": Decimal("10.00"),
        "gold": Decimal("5.00"),
        "cash": Decimal("0.00"),
    },
}

# ------------------------------------------------------------------------------
# 3. Permissible Risk Levels per User Risk Profile
# ------------------------------------------------------------------------------
ALLOWED_PRODUCT_RISK_MAP = {
    "CONSERVATIVE": {"low", "moderate"},
    "MODERATE": {"low", "moderate", "high"},
    "AGGRESSIVE": {"low", "moderate", "high", "very_high"},
    "VERY_AGGRESSIVE": {"low", "moderate", "high", "very_high"},
}

# ------------------------------------------------------------------------------
# 4. Tolerances and Constraints
# ------------------------------------------------------------------------------
ALLOCATION_TOLERANCE_PCT: Decimal = Decimal("0.50")  # ±0.5% allowed drift for rounding
MINIMUM_SIP_AMOUNT_FLOOR: Decimal = Decimal("500.00")  # Minimum meaningful SIP in INR
MAX_PRODUCTS_PER_PORTFOLIO: int = 6
MIN_PRODUCTS_PER_PORTFOLIO: int = 2
