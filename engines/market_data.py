"""
engines/market_data.py — Market Data Fetcher
Fetches NSE/BSE stock data via Yahoo Finance.
Uses in-memory cache (works on Render — no SQLite needed).
"""

import httpx
import asyncio
from datetime import datetime
from typing import Optional
import logging

from database.models import cache_get, cache_set

logger = logging.getLogger(__name__)

CACHE_TTL = 15  # minutes


async def fetch_stock_quote(symbol: str) -> dict:
    """Fetch real-time quote. Tries NSE (.NS) then BSE (.BO)."""
    cache_key = f"quote:{symbol}"
    cached    = cache_get(cache_key)
    if cached:
        return cached

    for suffix in [".NS", ".BO"]:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}{suffix}"
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params={"interval": "1d", "range": "5d"})
                resp.raise_for_status()
                data = resp.json()

            result = _parse_quote(data, symbol)
            if result:
                cache_set(cache_key, result, CACHE_TTL)
                return result
        except Exception as e:
            logger.debug(f"Quote failed {symbol}{suffix}: {e}")
            continue

    raise ValueError(f"Symbol not found: {symbol}. Check NSE/BSE symbol and retry.")


def _parse_quote(data: dict, symbol: str) -> Optional[dict]:
    try:
        res    = data["chart"]["result"][0]
        meta   = res["meta"]
        price  = meta.get("regularMarketPrice", 0)
        prev   = meta.get("chartPreviousClose", price)
        change = round(price - prev, 2)

        return {
            "symbol":       symbol,
            "name":         meta.get("longName") or meta.get("shortName") or symbol,
            "exchange":     meta.get("exchangeName", "NSE"),
            "price":        round(price, 2),
            "prev_close":   round(prev, 2),
            "change":       change,
            "change_pct":   round((change / prev) * 100, 2) if prev else 0,
            "volume":       meta.get("regularMarketVolume", 0),
            "market_cap":   meta.get("marketCap", 0),
            "week_52_high": round(meta.get("fiftyTwoWeekHigh", 0), 2),
            "week_52_low":  round(meta.get("fiftyTwoWeekLow",  0), 2),
            "day_high":     meta.get("regularMarketDayHigh", price),
            "day_low":      meta.get("regularMarketDayLow",  price),
        }
    except Exception as e:
        logger.error(f"Parse quote error: {e}")
        return None


async def fetch_fundamentals(symbol: str) -> dict:
    """Fetch P/E, ROE, D/E etc. Cached for 60 min."""
    cache_key = f"fund:{symbol}"
    cached    = cache_get(cache_key)
    if cached:
        return cached

    for suffix in [".NS", ".BO"]:
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}{suffix}"
            params = {"modules": "summaryDetail,defaultKeyStatistics,financialData"}
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            result = _parse_fundamentals(data)
            if result:
                cache_set(cache_key, result, 60)
                return result
        except Exception as e:
            logger.debug(f"Fundamentals failed {symbol}{suffix}: {e}")
            continue

    return {}


def _parse_fundamentals(data: dict) -> dict:
    try:
        summary = data["quoteSummary"]["result"][0]
        sd  = summary.get("summaryDetail", {})
        ks  = summary.get("defaultKeyStatistics", {})
        fd  = summary.get("financialData", {})

        def v(d, k):
            val = d.get(k, {})
            return val.get("raw") if isinstance(val, dict) else val

        return {
            "pe_ratio":       round(v(sd, "trailingPE") or 0, 2),
            "forward_pe":     round(v(sd, "forwardPE") or 0, 2),
            "eps":            round(v(ks, "trailingEps") or 0, 2),
            "book_value":     round(v(ks, "bookValue") or 0, 2),
            "price_to_book":  round(v(ks, "priceToBook") or 0, 2),
            "dividend_yield": round((v(sd, "dividendYield") or 0) * 100, 2),
            "roe":            round((v(fd, "returnOnEquity") or 0) * 100, 2),
            "debt_to_equity": round(v(fd, "debtToEquity") or 0, 2),
            "revenue_growth": round((v(fd, "revenueGrowth") or 0) * 100, 2),
            "earnings_growth":round((v(fd, "earningsGrowth") or 0) * 100, 2),
            "profit_margin":  round((v(fd, "profitMargins") or 0) * 100, 2),
            "current_ratio":  round(v(fd, "currentRatio") or 0, 2),
        }
    except Exception as e:
        logger.error(f"Parse fundamentals error: {e}")
        return {}


async def fetch_market_indices() -> dict:
    """SENSEX, NIFTY, BANKNIFTY, GOLD, USD/INR."""
    indices = {
        "SENSEX":     "^BSESN",
        "NIFTY_50":   "^NSEI",
        "BANK_NIFTY": "^NSEBANK",
        "GOLD_INR":   "GC=F",
        "USD_INR":    "USDINR=X",
    }
    results = {}
    tasks   = [fetch_stock_quote(ticker) for ticker in indices.values()]
    quotes  = await asyncio.gather(*tasks, return_exceptions=True)

    for (name, _), quote in zip(indices.items(), quotes):
        if isinstance(quote, dict):
            results[name] = {
                "price":      quote.get("price"),
                "change":     quote.get("change"),
                "change_pct": quote.get("change_pct"),
            }
    return results
