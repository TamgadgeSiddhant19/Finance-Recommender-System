from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------------------
# 1. Domain Enums
# ------------------------------------------------------------------------------
class ProductType(str, Enum):
    mutual_fund = "mutual_fund"
    etf = "etf"
    stock = "stock"
    bond = "bond"
    fixed_deposit = "fixed_deposit"
    government_security = "government_security"
    index_fund = "index_fund"
    gold = "gold"
    other = "other"


class AssetClass(str, Enum):
    equity = "equity"
    debt = "debt"
    gold = "gold"
    cash = "cash"
    hybrid = "hybrid"
    other = "other"


class ProductRiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    very_high = "very_high"


# ------------------------------------------------------------------------------
# 2. Financial Product Schemas
# ------------------------------------------------------------------------------
class FinancialProductBase(BaseModel):
    symbol: str = Field(..., max_length=50, description="Unique instrument ticker or symbol")
    name: str = Field(..., max_length=255, description="Full descriptive name of the financial product")
    product_type: ProductType = Field(..., description="Classification category of the product")
    asset_class: AssetClass = Field(..., description="Broad asset class")
    issuer: str = Field(..., max_length=255, description="Issuing entity, fund house, or institution")
    currency: str = Field(default="INR", max_length=10, description="Denomination currency code")
    country: str = Field(default="India", max_length=50, description="Country of origin / domicile")
    risk_level: ProductRiskLevel = Field(..., description="Internal prototype risk level indicator")
    expense_ratio: Optional[Decimal] = Field(default=None, ge=0, le=1, description="Annual management/expense ratio fraction")
    minimum_investment: Decimal = Field(default=Decimal("500.00"), ge=0, description="Minimum investment amount in currency")


class FinancialProductCreate(FinancialProductBase):
    pass


class FinancialProductResponse(FinancialProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# 3. Market Data Schemas
# ------------------------------------------------------------------------------
class MarketDataBase(BaseModel):
    timestamp: datetime = Field(..., description="Date & time of the market price observation (UTC)")
    open_price: Decimal = Field(..., ge=0, description="Opening price in local currency")
    high_price: Decimal = Field(..., ge=0, description="Highest traded price in local currency")
    low_price: Decimal = Field(..., ge=0, description="Lowest traded price in local currency")
    close_price: Decimal = Field(..., ge=0, description="Closing price or NAV in local currency")
    volume: int = Field(default=0, ge=0, description="Trading volume or units traded")
    source: str = Field(default="demo/synthetic", max_length=50, description="Data source origin tag")


class MarketDataCreate(MarketDataBase):
    financial_product_id: Optional[int] = None
    symbol: Optional[str] = None  # Facilitates ingestion by symbol before ID lookup


class MarketDataResponse(MarketDataBase):
    id: int
    financial_product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# 4. Ingestion Result Schema
# ------------------------------------------------------------------------------
class IngestionSummary(BaseModel):
    status: str = "success"
    products_processed: int = 0
    products_created: int = 0
    products_updated: int = 0
    market_records_processed: int = 0
    market_records_created: int = 0
    market_records_updated: int = 0
    errors: List[str] = Field(default_factory=list)
