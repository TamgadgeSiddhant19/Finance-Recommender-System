import os
from pathlib import Path
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_data.adapters.csv_adapter import CSVAdapter
from app.financial_data.repository import FinancialProductRepository
from app.financial_data.schemas import IngestionSummary


class IngestionService:
    """
    Orchestrates the ingestion, validation, normalization, and idempotent storage
    of financial products and market time series.
    """

    def __init__(self, db: AsyncSession, adapter: Optional[CSVAdapter] = None):
        self.repo = FinancialProductRepository(db)
        self.adapter = adapter or CSVAdapter()

    async def ingest_from_csv(
        self,
        products_source: Union[str, Path],
        market_data_source: Optional[Union[str, Path]] = None,
    ) -> IngestionSummary:
        """
        Execute full end-to-end ingestion from CSV sources.
        """
        summary = IngestionSummary()

        # ----------------------------------------------------------------------
        # 1. Ingest Financial Products
        # ----------------------------------------------------------------------
        if not os.path.exists(str(products_source)):
            summary.status = "error"
            summary.errors.append(f"Products file not found at path: {products_source}")
            return summary

        products, prod_errors = self.adapter.load_products(products_source)
        summary.errors.extend(prod_errors)

        symbol_to_id = {}

        for prod in products:
            try:
                db_prod, created = await self.repo.upsert_product(prod)
                summary.products_processed += 1
                if created:
                    summary.products_created += 1
                else:
                    summary.products_updated += 1
                symbol_to_id[db_prod.symbol] = db_prod.id
            except Exception as e:
                summary.errors.append(f"Database error saving product {prod.symbol}: {str(e)}")

        # ----------------------------------------------------------------------
        # 2. Ingest Market Data (if provided)
        # ----------------------------------------------------------------------
        if market_data_source:
            if not os.path.exists(str(market_data_source)):
                summary.errors.append(f"Market data file not found at path: {market_data_source}")
            else:
                market_records, md_errors = self.adapter.load_market_data(market_data_source)
                summary.errors.extend(md_errors)

                for md_item in market_records:
                    # Look up product_id by symbol if not pre-populated
                    product_id = md_item.financial_product_id
                    if not product_id and md_item.symbol:
                        product_id = symbol_to_id.get(md_item.symbol)
                        if not product_id:
                            # Attempt repository lookup if not in local batch map
                            db_p = await self.repo.get_by_symbol(md_item.symbol)
                            if db_p:
                                product_id = db_p.id
                                symbol_to_id[md_item.symbol] = db_p.id

                    if not product_id:
                        summary.errors.append(
                            f"Skipping market record for unknown product symbol: {md_item.symbol}"
                        )
                        continue

                    try:
                        _, created = await self.repo.upsert_market_data(md_item, product_id)
                        summary.market_records_processed += 1
                        if created:
                            summary.market_records_created += 1
                        else:
                            summary.market_records_updated += 1
                    except Exception as e:
                        summary.errors.append(
                            f"Database error saving market data for {md_item.symbol} at {md_item.timestamp}: {str(e)}"
                        )

        if summary.errors and summary.products_processed == 0 and summary.market_records_processed == 0:
            summary.status = "failed"
        elif summary.errors:
            summary.status = "partial_success"
        else:
            summary.status = "success"

        return summary
