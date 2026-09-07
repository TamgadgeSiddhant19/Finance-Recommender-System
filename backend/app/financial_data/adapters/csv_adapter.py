import csv
import io
import os
from pathlib import Path
from typing import List, Tuple, Union
from app.financial_data.adapters.base import FinancialDataAdapter
from app.financial_data.normalizer import (
    normalize_market_data_dict,
    normalize_product_dict,
)
from app.financial_data.schemas import (
    FinancialProductCreate,
    MarketDataCreate,
)
from app.financial_data.validators import (
    validate_market_data,
    validate_product_data,
)


class CSVAdapter(FinancialDataAdapter):
    """
    Adapter for parsing, validating, and normalizing CSV financial datasets.
    """

    def _read_rows(self, source: Union[str, Path]) -> List[dict]:
        """Read CSV content from a file path or raw string."""
        source_str = str(source)
        if os.path.exists(source_str):
            with open(source_str, mode="r", encoding="utf-8-sig") as f_file:
                reader = csv.DictReader(f_file)
                return list(reader)
        else:
            # Treat as raw CSV string buffer
            f_str = io.StringIO(source_str.strip())
            reader = csv.DictReader(f_str)
            return list(reader)

    def load_products(self, source: Union[str, Path]) -> Tuple[List[FinancialProductCreate], List[str]]:
        """
        Parse and validate a financial products CSV source.
        """
        rows = self._read_rows(source)
        valid_products: List[FinancialProductCreate] = []
        errors: List[str] = []

        required_headers = {"symbol", "name", "product_type", "asset_class", "issuer", "risk_level"}

        for idx, row in enumerate(rows, start=2):  # Line 2 corresponds to first data row
            # 1. Check missing headers
            missing = required_headers - set(k.strip() for k in row.keys() if k)
            if missing:
                errors.append(f"Row {idx}: Missing required fields: {', '.join(missing)}")
                continue

            try:
                # 2. Normalize
                norm_product = normalize_product_dict(row)

                # 3. Validate
                is_valid, val_errors = validate_product_data(norm_product)
                if not is_valid:
                    errors.append(f"Row {idx} ({row.get('symbol', 'UNKNOWN')}): {'; '.join(val_errors)}")
                    continue

                valid_products.append(norm_product)
            except Exception as e:
                errors.append(f"Row {idx} parse error ({row.get('symbol', 'UNKNOWN')}): {str(e)}")

        return valid_products, errors

    def load_market_data(self, source: Union[str, Path]) -> Tuple[List[MarketDataCreate], List[str]]:
        """
        Parse and validate a market OHLCV price series CSV source.
        """
        rows = self._read_rows(source)
        valid_records: List[MarketDataCreate] = []
        errors: List[str] = []

        required_headers = {"symbol", "timestamp", "open_price", "high_price", "low_price", "close_price"}

        for idx, row in enumerate(rows, start=2):
            missing = required_headers - set(k.strip() for k in row.keys() if k)
            if missing:
                errors.append(f"Row {idx}: Missing required fields: {', '.join(missing)}")
                continue

            try:
                # 2. Normalize
                norm_record = normalize_market_data_dict(row)

                # 3. Validate
                is_valid, val_errors = validate_market_data(norm_record)
                if not is_valid:
                    errors.append(f"Row {idx} ({row.get('symbol', 'UNKNOWN')} @ {row.get('timestamp')}): {'; '.join(val_errors)}")
                    continue

                valid_records.append(norm_record)
            except Exception as e:
                errors.append(f"Row {idx} parse error ({row.get('symbol', 'UNKNOWN')}): {str(e)}")

        return valid_records, errors
