# Financial Product and Market Data Layer

The **Financial Product and Market Data Layer** provides a normalized, decoupled data access foundation for the AI Finance Recommendation System.

---

## 🏗️ Architecture & Data Flow

The system uses an **Adapter Pattern** to isolate database models and recommendation logic from external data providers (CSV files, exchange feeds, vendor APIs):

```
External Source (CSV / API)
            ↓
FinancialDataAdapter (Base Interface)
            ↓
CSVAdapter / FutureMarketAPIAdapter
            ↓
Validators (Verify OHLCV bounds, positive prices, enums)
            ↓
Normalizer (Standardize symbols, trim whitespace, Decimal conversion)
            ↓
FinancialProductRepository (Idempotent Upsert & Querying)
            ↓
PostgreSQL Database (financial_products, market_data)
            ↓
Recommendation Engine & Research Agent (Future Phases)
```

### Key Design Benefits
1. **Decoupled Business Logic**: The recommendation engine interacts exclusively with internal repository methods and normalized models rather than external provider schemas.
2. **Pluggable Data Adapters**: Transitioning from CSV development feeds to live market APIs (e.g. NSE/BSE feeds or vendor REST APIs) requires only adding a new `FinancialDataAdapter` subclass without touching API endpoints or database schemas.
3. **Financial Math Safety**: Prices, expense ratios, and minimum investments are stored strictly as `NUMERIC / Decimal` to eliminate floating-point rounding errors.

---

## 🗄️ Database Schema

### 1. `financial_products` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, `AUTOINCREMENT` | Unique product identifier |
| `symbol` | `VARCHAR(50)` | `UNIQUE`, `NOT NULL`, `INDEX` | Instrument ticker or identifier |
| `name` | `VARCHAR(255)` | `NOT NULL` | Descriptive name |
| `product_type` | `VARCHAR(50)` | `NOT NULL`, `INDEX` | `mutual_fund`, `etf`, `stock`, `bond`, `fixed_deposit`, `government_security`, `index_fund`, `gold`, `other` |
| `asset_class` | `VARCHAR(50)` | `NOT NULL`, `INDEX` | `equity`, `debt`, `gold`, `cash`, `hybrid`, `other` |
| `issuer` | `VARCHAR(255)` | `NOT NULL` | Fund house or issuing entity |
| `currency` | `VARCHAR(10)` | `NOT NULL`, `DEFAULT 'INR'` | Denomination currency |
| `country` | `VARCHAR(50)` | `NOT NULL`, `DEFAULT 'India'` | Country of domicile |
| `risk_level` | `VARCHAR(50)` | `NOT NULL`, `INDEX` | `low`, `moderate`, `high`, `very_high` |
| `expense_ratio` | `NUMERIC(5, 4)` | `NULLABLE` | Annual management fee fraction |
| `minimum_investment` | `NUMERIC(14, 2)` | `NOT NULL`, `DEFAULT 500.00` | Minimum initial purchase in INR |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Last update timestamp |

### 2. `market_data` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, `AUTOINCREMENT` | Record identifier |
| `financial_product_id` | `INTEGER` | `FOREIGN KEY (financial_products.id) ON DELETE CASCADE`, `INDEX` | Associated financial product |
| `timestamp` | `TIMESTAMPTZ` | `NOT NULL`, `INDEX` | Observation timestamp (UTC) |
| `open_price` | `NUMERIC(14, 2)` | `NOT NULL` | Opening price in INR |
| `high_price` | `NUMERIC(14, 2)` | `NOT NULL` | Highest price in INR |
| `low_price` | `NUMERIC(14, 2)` | `NOT NULL` | Lowest price in INR |
| `close_price` | `NUMERIC(14, 2)` | `NOT NULL` | Closing price / NAV in INR |
| `volume` | `BIGINT` | `NOT NULL`, `DEFAULT 0` | Volume / units traded |
| `source` | `VARCHAR(50)` | `NOT NULL`, `DEFAULT 'demo/synthetic'` | Data origin tag |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |

- **Composite Constraints**:
  - `UniqueConstraint("financial_product_id", "timestamp")` guarantees idempotency on ingestion.
  - Compound index `ix_market_data_product_timestamp` ensures sub-millisecond historical queries.

---

## 📥 Ingestion & Idempotency Pipeline

1. **Extraction**: `CSVAdapter` parses `data/financial_products.csv` and `data/market_data.csv`.
2. **Validation**: Enforces non-negative prices, OHLC invariants ($Low \le Open \le High$, $Low \le Close \le High$), enum compliance, and positive minimum investments.
3. **Normalization**: Standardizes symbols, trims whitespace, and quantizes decimals.
4. **Idempotent Upsert**:
   - Products are matched on `symbol`. Existing products are updated in-place; new products are inserted.
   - Market data records are matched on `(financial_product_id, timestamp)`. Re-running ingestion never creates duplicate records.

---

## ⚠️ Financial Safety & Prototype Notice

- **Prototype Status**: This platform is an engineering and AI prototype.
- **Synthetic Data**: All development market price data and instruments are synthetic demo representations.
- **No Performance Guarantees**: Historical or synthetic numbers do not guarantee future returns.
- **No Direct Execution**: The system does not execute live trades or automatic buy/sell orders.
