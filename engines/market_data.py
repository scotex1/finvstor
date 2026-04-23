"""
engines/market_data.py — Market Data Fetcher
Fetches stock quotes, fundamentals, and NSE/BSE data.
Uses yfinance (free) + cache layer to avoid rate limits.
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# ── Simple in-memory cache ────────────────────────────────
_cache: dict = {}
CACHE_TTL_MINUTES = 15


def _cache_get(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if not entry:
        return None
    if datetime.utcnow() > entry["expires"]:
        del _cache[key]
        return None
    return entry["data"]


def _cache_set(key: str, data: dict, ttl_minutes: int = CACHE_TTL_MINUTES):
    _cache[key] = {
        "data":    data,
        "expires": datetime.utcnow() + timedelta(minutes=ttl_minutes),
    }


# ── Yahoo Finance via yfinance HTTP API ──────────────────
async def fetch_stock_quote(symbol: str) -> dict:
    """
    Fetch real-time quote for NSE/BSE stock.
    symbol: e.g. "RELIANCE" → tries "RELIANCE.NS" for NSE
    """
    cache_key = f"quote:{symbol}"
    cached    = _cache_get(cache_key)
    if cached:
        return cached

    # Try NSE suffix first, then BSE
    suffixes = [".NS", ".BO"]
    for suffix in suffixes:
        try:
            url  = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}{suffix}"
            params = {"interval": "1d", "range": "5d"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            result = _parse_yahoo_quote(data, symbol)
            if result:
                _cache_set(cache_key, result)
                return result
        except Exception as e:
            logger.debug(f"Yahoo quote failed for {symbol}{suffix}: {e}")
            continue

    raise ValueError(f"Could not fetch data for symbol: {symbol}")


def _parse_yahoo_quote(data: dict, symbol: str) -> Optional[dict]:
    try:
        result  = data["chart"]["result"][0]
        meta    = result["meta"]
        quotes  = result.get("indicators", {}).get("quote", [{}])[0]
        closes  = quotes.get("close", [])
        current = meta.get("regularMarketPrice", 0)
        prev    = meta.get("chartPreviousClose", current)

        change     = round(current - prev, 2)
        change_pct = round((change / prev) * 100, 2) if prev else 0

        # 52 week high/low
        w52_high = meta.get("fiftyTwoWeekHigh", 0)
        w52_low  = meta.get("fiftyTwoWeekLow",  0)

        return {
            "symbol":     symbol,
            "name":       meta.get("longName") or meta.get("shortName") or symbol,
            "exchange":   meta.get("exchangeName", "NSE"),
            "currency":   meta.get("currency", "INR"),
            "price":      round(current, 2),
            "prev_close": round(prev, 2),
            "change":     change,
            "change_pct": change_pct,
            "volume":     meta.get("regularMarketVolume", 0),
            "market_cap": meta.get("marketCap", 0),
            "week_52_high": round(w52_high, 2),
            "week_52_low":  round(w52_low, 2),
            "day_high":  meta.get("regularMarketDayHigh", current),
            "day_low":   meta.get("regularMarketDayLow",  current),
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error parsing Yahoo quote: {e}")
        return None


async def fetch_fundamentals(symbol: str) -> dict:
    """
    Fetch fundamental data: P/E, EPS, dividend yield, etc.
    Uses Yahoo Finance summary endpoint.
    """
    cache_key = f"fundamentals:{symbol}"
    cached    = _cache_get(cache_key)
    if cached:
        return cached

    suffixes = [".NS", ".BO"]
    for suffix in suffixes:
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}{suffix}"
            params = {"modules": "summaryDetail,defaultKeyStatistics,financialData"}
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            result = _parse_fundamentals(data)
            if result:
                _cache_set(cache_key, result, ttl_minutes=60)  # Cache 1 hour
                return result
        except Exception as e:
            logger.debug(f"Fundamentals fetch failed for {symbol}{suffix}: {e}")
            continue

    return {}  # Return empty — not critical


def _parse_fundamentals(data: dict) -> dict:
    try:
        summary = data.get("quoteSummary", {}).get("result", [{}])[0]
        sd  = summary.get("summaryDetail", {})
        ks  = summary.get("defaultKeyStatistics", {})
        fd  = summary.get("financialData", {})

        def val(d, key):
            v = d.get(key, {})
            return v.get("raw") if isinstance(v, dict) else v

        return {
            "pe_ratio":         round(val(sd, "trailingPE") or 0, 2),
            "forward_pe":       round(val(sd, "forwardPE") or 0, 2),
            "eps":              round(val(ks, "trailingEps") or 0, 2),
            "book_value":       round(val(ks, "bookValue") or 0, 2),
            "price_to_book":    round(val(ks, "priceToBook") or 0, 2),
            "dividend_yield":   round((val(sd, "dividendYield") or 0) * 100, 2),
            "roe":              round((val(fd, "returnOnEquity") or 0) * 100, 2),
            "debt_to_equity":   round(val(fd, "debtToEquity") or 0, 2),
            "revenue_growth":   round((val(fd, "revenueGrowth") or 0) * 100, 2),
            "earnings_growth":  round((val(fd, "earningsGrowth") or 0) * 100, 2),
            "profit_margin":    round((val(fd, "profitMargins") or 0) * 100, 2),
            "current_ratio":    round(val(fd, "currentRatio") or 0, 2),
            "free_cashflow":    val(fd, "freeCashflow") or 0,
        }
    except Exception as e:
        logger.error(f"Error parsing fundamentals: {e}")
        return {}


async def fetch_market_indices() -> dict:
    """Fetch SENSEX, NIFTY, BANKNIFTY, GOLD, USD/INR."""
    indices = {
        "SENSEX":    "^BSESN",
        "NIFTY_50":  "^NSEI",
        "BANK_NIFTY": "^NSEBANK",
        "GOLD_INR":  "GC=F",
        "USD_INR":   "USDINR=X",
    }
    result = {}
    tasks  = [fetch_stock_quote(ticker) for ticker in indices.values()]
    quotes = await asyncio.gather(*tasks, return_exceptions=True)

    for (name, _), quote in zip(indices.items(), quotes):
        if isinstance(quote, dict):
            result[name] = {
                "price":      quote.get("price"),
                "change":     quote.get("change"),
                "change_pct": quote.get("change_pct"),
            }

    return result
