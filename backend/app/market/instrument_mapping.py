"""
Centralized Instrument Mapping Layer.
Decouples internal canonical asset symbols from provider-specific identifiers.
"""

from typing import Dict, List, Optional
from app.market.schemas import InstrumentInfo


class InstrumentMapper:
    """
    Registry for translating between internal application symbols (e.g., 'TCS', 'NIFTY 50')
    and provider-specific instrument keys (e.g., 'NSE_EQ|INE467B01029', 'NSE_INDEX|Nifty 50').
    """

    # Static Development / Benchmark Instrument Mappings
    # Clearly documented as development mappings until verified against live broker instrument master.
    DEFAULT_INSTRUMENTS: Dict[str, InstrumentInfo] = {
        # Core Benchmark Indices
        "NIFTY 50": InstrumentInfo(
            symbol="NIFTY 50",
            name="NIFTY 50 Index",
            exchange="NSE",
            instrument_type="INDEX",
            provider_key="NSE_INDEX|Nifty 50",
            is_active=True,
            data_source="development_mapping",
        ),
        "NIFTY BANK": InstrumentInfo(
            symbol="NIFTY BANK",
            name="NIFTY Bank Index",
            exchange="NSE",
            instrument_type="INDEX",
            provider_key="NSE_INDEX|Nifty Bank",
            is_active=True,
            data_source="development_mapping",
        ),
        "SENSEX": InstrumentInfo(
            symbol="SENSEX",
            name="BSE Sensex Index",
            exchange="BSE",
            instrument_type="INDEX",
            provider_key="BSE_INDEX|SENSEX",
            is_active=True,
            data_source="development_mapping",
        ),
        "INDIA VIX": InstrumentInfo(
            symbol="INDIA VIX",
            name="India Volatility Index",
            exchange="NSE",
            instrument_type="INDEX",
            provider_key="NSE_INDEX|India VIX",
            is_active=True,
            data_source="development_mapping",
        ),
        # Major Equities (Development Mappings with Standard NSE ISINs)
        "TCS": InstrumentInfo(
            symbol="TCS",
            name="Tata Consultancy Services Ltd",
            exchange="NSE",
            instrument_type="EQUITY",
            provider_key="NSE_EQ|INE467B01029",
            is_active=True,
            data_source="development_mapping",
        ),
        "INFY": InstrumentInfo(
            symbol="INFY",
            name="Infosys Ltd",
            exchange="NSE",
            instrument_type="EQUITY",
            provider_key="NSE_EQ|INE009A01021",
            is_active=True,
            data_source="development_mapping",
        ),
        "RELIANCE": InstrumentInfo(
            symbol="RELIANCE",
            name="Reliance Industries Ltd",
            exchange="NSE",
            instrument_type="EQUITY",
            provider_key="NSE_EQ|INE002A01018",
            is_active=True,
            data_source="development_mapping",
        ),
        "HDFCBANK": InstrumentInfo(
            symbol="HDFCBANK",
            name="HDFC Bank Ltd",
            exchange="NSE",
            instrument_type="EQUITY",
            provider_key="NSE_EQ|INE040A01034",
            is_active=True,
            data_source="development_mapping",
        ),
        "ICICIBANK": InstrumentInfo(
            symbol="ICICIBANK",
            name="ICICI Bank Ltd",
            exchange="NSE",
            instrument_type="EQUITY",
            provider_key="NSE_EQ|INE090A01021",
            is_active=True,
            data_source="development_mapping",
        ),
        # ETFs
        "GOLDBEES": InstrumentInfo(
            symbol="GOLDBEES",
            name="Nippon India ETF Gold BeES",
            exchange="NSE",
            instrument_type="ETF",
            provider_key="NSE_EQ|INF732E01037",
            is_active=True,
            data_source="development_mapping",
        ),
        "NIFTYBEES": InstrumentInfo(
            symbol="NIFTYBEES",
            name="Nippon India ETF Nifty 50 BeES",
            exchange="NSE",
            instrument_type="ETF",
            provider_key="NSE_EQ|INF732E01011",
            is_active=True,
            data_source="development_mapping",
        ),
        "LIQUIDBEES": InstrumentInfo(
            symbol="LIQUIDBEES",
            name="Nippon India ETF Liquid BeES",
            exchange="NSE",
            instrument_type="ETF",
            provider_key="NSE_EQ|INF732E01029",
            is_active=True,
            data_source="development_mapping",
        ),
    }

    def __init__(self, custom_instruments: Optional[Dict[str, InstrumentInfo]] = None):
        self._registry: Dict[str, InstrumentInfo] = dict(self.DEFAULT_INSTRUMENTS)
        if custom_instruments:
            self._registry.update(custom_instruments)

        # Build reverse index: provider_key -> internal_symbol
        self._reverse_registry: Dict[str, str] = {}
        self._rebuild_reverse_index()

    def _rebuild_reverse_index(self) -> None:
        self._reverse_registry = {
            info.provider_key: symbol for symbol, info in self._registry.items()
        }

    def normalize_symbol(self, symbol_or_key: str) -> str:
        """
        Normalizes a symbol string (e.g. 'tcs', 'NIFTY_50', 'NSE_INDEX|Nifty 50')
        to canonical internal symbol (e.g. 'TCS', 'NIFTY 50').
        """
        cleaned = symbol_or_key.strip()
        # Direct lookup
        upper = cleaned.upper()
        if upper in self._registry:
            return upper

        # Replace underscores with spaces (e.g. NIFTY_50 -> NIFTY 50)
        spaced = upper.replace("_", " ")
        if spaced in self._registry:
            return spaced

        # Check reverse registry (provider key -> symbol)
        if cleaned in self._reverse_registry:
            return self._reverse_registry[cleaned]

        # Upstox colon separator fallback (e.g. NSE_INDEX:Nifty 50 -> NSE_INDEX|Nifty 50)
        pipe_version = cleaned.replace(":", "|")
        if pipe_version in self._reverse_registry:
            return self._reverse_registry[pipe_version]

        return upper

    def get_instrument_info(self, symbol_or_key: str) -> Optional[InstrumentInfo]:
        """Lookup InstrumentInfo by symbol or provider key."""
        canonical = self.normalize_symbol(symbol_or_key)
        return self._registry.get(canonical)

    def get_provider_key(self, symbol_or_key: str, default_if_missing: bool = True) -> str:
        """
        Get the provider-specific instrument key for a given symbol.
        If missing and default_if_missing is True, synthesizes a fallback NSE key.
        """
        canonical = self.normalize_symbol(symbol_or_key)
        info = self._registry.get(canonical)
        if info:
            return info.provider_key
        if default_if_missing:
            # Generate a standard NSE equity provider key format
            return f"NSE_EQ|{canonical}"
        return symbol_or_key

    def get_canonical_symbol(self, provider_key: str) -> str:
        """Get canonical internal symbol from provider key."""
        return self.normalize_symbol(provider_key)

    def list_all_instruments(self) -> List[InstrumentInfo]:
        """Return all registered instruments."""
        return list(self._registry.values())

    def register_instrument(self, info: InstrumentInfo) -> None:
        """Register or update an instrument mapping."""
        self._registry[info.symbol.upper()] = info
        self._reverse_registry[info.provider_key] = info.symbol.upper()


# Default global mapper instance
default_instrument_mapper = InstrumentMapper()
