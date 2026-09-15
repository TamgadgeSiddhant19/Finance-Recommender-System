"""
Market Data Domain Exceptions.
"""


class MarketDataError(Exception):
    """Base exception for all market data related errors."""

    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.provider = provider


class InstrumentNotFoundError(MarketDataError):
    """Raised when an internal symbol or provider instrument key cannot be resolved."""

    def __init__(self, symbol: str, provider: str = "unknown"):
        super().__init__(f"Instrument '{symbol}' could not be resolved or found.", provider)
        self.symbol = symbol


class ProviderUnavailableError(MarketDataError):
    """Raised when a market data provider is unreachable, offline, or timed out."""

    def __init__(self, provider: str, reason: str = "Provider service unreachable"):
        super().__init__(f"Market data provider '{provider}' is currently unavailable: {reason}", provider)
        self.reason = reason


class ProviderAuthenticationError(MarketDataError):
    """Raised when provider credentials/tokens are invalid or expired."""

    def __init__(self, provider: str, details: str = "Invalid or expired access token"):
        super().__init__(f"Authentication failed for market provider '{provider}': {details}", provider)
        self.details = details
