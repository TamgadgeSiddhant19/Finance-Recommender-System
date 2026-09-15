"""
Deterministic Market Intelligence Analytics.
Pure Python mathematical computations for technical and risk indicators.
Zero LLM involvement — strictly deterministic, verifiable, and unit-tested.
"""

from decimal import Decimal
import math
from typing import List, Optional, Tuple
from app.market.schemas import HistoricalCandle


def calculate_returns(prices: List[Decimal]) -> Decimal:
    """
    Computes total percentage return over a sequence of prices:
    Return = ((P_end - P_start) / P_start) * 100
    """
    if not prices or len(prices) < 2:
        return Decimal("0.00")

    start_price = prices[0]
    end_price = prices[-1]

    if start_price <= Decimal("0.00"):
        return Decimal("0.00")

    pct_return = ((end_price - start_price) / start_price) * Decimal("100")
    return round(pct_return, 4)


def calculate_volatility(prices: List[Decimal], annualize: bool = True, trading_days: int = 252) -> Decimal:
    """
    Calculates sample standard deviation of periodic percentage returns.
    If annualize is True, multiplies by sqrt(trading_days).
    """
    if not prices or len(prices) < 3:
        return Decimal("0.00")

    # Periodic returns
    returns: List[float] = []
    for i in range(1, len(prices)):
        prev = float(prices[i - 1])
        curr = float(prices[i])
        if prev > 0:
            returns.append((curr - prev) / prev)

    if len(returns) < 2:
        return Decimal("0.00")

    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = math.sqrt(variance)

    if annualize:
        std_dev *= math.sqrt(trading_days)

    return Decimal(f"{std_dev * 100:.4f}")


def calculate_moving_average(prices: List[Decimal], window: int = 20) -> List[Decimal]:
    """
    Calculates Simple Moving Average (SMA) series for a given window size.
    Returns a list of SMA values aligned with the price series.
    Initial values before full window is reached use expanding average.
    """
    if not prices or window <= 0:
        return []

    sma_series: List[Decimal] = []
    for i in range(len(prices)):
        start_idx = max(0, i - window + 1)
        subset = prices[start_idx : i + 1]
        avg = sum(subset) / Decimal(str(len(subset)))
        sma_series.append(round(avg, 2))

    return sma_series


def calculate_rsi(prices: List[Decimal], period: int = 14) -> Decimal:
    """
    Calculates Relative Strength Index (RSI) using standard Wilder smoothing.
    Returns a value between 0 and 100 (default 50.00 if insufficient data).
    """
    if not prices or len(prices) <= period:
        return Decimal("50.00")

    # Calculate price changes
    changes = [float(prices[i] - prices[i - 1]) for i in range(1, len(prices))]

    gains = [max(0.0, c) for c in changes]
    losses = [max(0.0, -c) for c in changes]

    # Initial average gain & loss over first 'period'
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Smoothed averages
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0.0:
        return Decimal("100.00") if avg_gain > 0 else Decimal("50.00")

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return Decimal(f"{rsi:.2f}")


def calculate_drawdown(prices: List[Decimal]) -> Tuple[Decimal, Decimal]:
    """
    Calculates (max_drawdown_percent, current_drawdown_percent) from a price series.
    Drawdown = (Current_Price - Peak_Price) / Peak_Price * 100
    Max Drawdown is the largest percentage drop from a peak.
    """
    if not prices:
        return Decimal("0.00"), Decimal("0.00")

    peak = prices[0]
    max_dd = Decimal("0.00")

    for p in prices:
        if p > peak:
            peak = p
        if peak > Decimal("0.00"):
            dd = ((p - peak) / peak) * Decimal("100")
            if dd < max_dd:
                max_dd = dd

    # Current drawdown
    current_price = prices[-1]
    curr_dd = ((current_price - peak) / peak * Decimal("100")) if peak > Decimal("0.00") else Decimal("0.00")

    return round(max_dd, 2), round(curr_dd, 2)


def calculate_52_week_range(candles: List[HistoricalCandle]) -> Tuple[Decimal, Decimal]:
    """
    Calculates (52_week_low, 52_week_high) from historical candles.
    """
    if not candles:
        return Decimal("0.00"), Decimal("0.00")

    low_val = min(c.low for c in candles)
    high_val = max(c.high for c in candles)
    return round(low_val, 2), round(high_val, 2)


def calculate_volume_change(candles: List[HistoricalCandle], window: int = 5) -> Decimal:
    """
    Calculates volume percentage change between the latest candle and the rolling volume average.
    """
    if not candles or len(candles) < 2 or window <= 0:
        return Decimal("0.00")

    recent_vol = candles[-1].volume
    prior_candles = candles[-(window + 1) : -1] if len(candles) > window else candles[:-1]

    if not prior_candles:
        return Decimal("0.00")

    avg_prior_vol = sum(c.volume for c in prior_candles) / len(prior_candles)
    if avg_prior_vol == 0:
        return Decimal("0.00")

    vol_change_pct = ((recent_vol - avg_prior_vol) / avg_prior_vol) * 100
    return Decimal(f"{vol_change_pct:.2f}")
