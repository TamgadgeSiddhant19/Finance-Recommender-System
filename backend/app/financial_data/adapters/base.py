from abc import ABC, abstractmethod
from typing import List, Tuple
from app.financial_data.schemas import (
    FinancialProductCreate,
    MarketDataCreate,
)


class FinancialDataAdapter(ABC):
    """
    Abstract interface for financial data adapters.
    Allows seamlessly connecting CSV files, mock feeds, or future live market APIs
    without changing the database repository or recommendation engine.
    """

    @abstractmethod
    def load_products(self, source: str) -> Tuple[List[FinancialProductCreate], List[str]]:
        """
        Extract, validate, and normalize financial products from the given source.
        Returns a tuple of (valid_records, error_messages).
        """
        pass

    @abstractmethod
    def load_market_data(self, source: str) -> Tuple[List[MarketDataCreate], List[str]]:
        """
        Extract, validate, and normalize historical market prices from the given source.
        Returns a tuple of (valid_records, error_messages).
        """
        pass
