"""
engines/stock_analysis.py — Stock Analysis Engine (PRO)
Fundamental + Technical analysis with AI-generated summary
Uses: yfinance for data, rule-based technicals, optional LLM for summary
"""

import asyncio
from engines.market_data import fetch_stock_quote, fetch_fundamentals
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class StockAnalysisEngine:

    @staticmethod
    async def analyze(symbol: str) -> dict:
        """
        Full stock analysis:
        1. Fetch quote + fundamentals in parallel
        2. Calculate technical signals
        3. Generate buy/hold/sell verdict
        4. AI summary (if configured)
        """
        # Parallel fetch
        quote_task = fetch_stock_quote(symbol)
        fund_task  = fetch_fundamentals(symbol)
        quote, fundamentals = await asyncio.gather(
            quote_task, fund_task, return_exceptions=True
        )

        if isinstance(quote, Exception):
            raise ValueError(f"Could not find stock: {symbol}. Check the symbol and try again.")

        if isinstance(fundamentals, Exception):
            fundamentals = {}

        # Technical signals (rule-based)
        technicals = StockAnalysisEngine._technicals(quote, fundamentals)

        # Verdict
        verdict = StockAnalysisEngine._verdict(fundamentals, technicals)

        # AI summary
        ai_summary = await StockAnalysisEngine._ai_summary(
            symbol, quote, fundamentals, technicals, verdict
        )

        # Format market cap
        mcap = quote.get("market_cap", 0)
        if mcap >= 1e12:
            mcap_str = f"₹{mcap/1e12:.1f}L Cr"
        elif mcap >= 1e9:
            mcap_str = f"₹{mcap/1e9:.0f}K Cr"
        elif mcap >= 1e7:
            mcap_str = f"₹{mcap/1e7:.0f} Cr"
        else:
            mcap_str = "N/A"

        return {
            # Quote data
            "symbol":       symbol,
            "name":         quote.get("name", symbol),
            "exchange":     quote.get("exchange", "NSE"),
            "price":        quote.get("price", 0),
            "prev_close":   quote.get("prev_close", 0),
            "change":       quote.get("change", 0),
            "change_pct":   quote.get("change_pct", 0),
            "day_high":     quote.get("day_high", 0),
            "day_low":      quote.get("day_low", 0),
            "week_52_high": quote.get("week_52_high", 0),
            "week_52_low":  quote.get("week_52_low", 0),
            "volume":       quote.get("volume", 0),
            "mcap":         mcap_str,
            # Fundamentals
            "pe":              fundamentals.get("pe_ratio", 0),
            "forward_pe":      fundamentals.get("forward_pe", 0),
            "eps":             fundamentals.get("eps", 0),
            "book_value":      fundamentals.get("book_value", 0),
            "price_to_book":   fundamentals.get("price_to_book", 0),
            "dividend_yield":  fundamentals.get("dividend_yield", 0),
            "roe":             fundamentals.get("roe", 0),
            "de":              fundamentals.get("debt_to_equity", 0),
            "revenue_growth":  fundamentals.get("revenue_growth", 0),
            "profit_growth":   fundamentals.get("earnings_growth", 0),
            "profit_margin":   fundamentals.get("profit_margin", 0),
            # Technicals
            "rsi":      technicals.get("rsi"),
            "rsi_signal": technicals.get("rsi_signal"),
            "macd":     technicals.get("macd"),
            "ma50":     technicals.get("ma50"),
            "ma200":    technicals.get("ma200"),
            "momentum": technicals.get("momentum"),
            # Verdict & Summary
            "verdict":    verdict,
            "ai_summary": ai_summary,
        }

    @staticmethod
    def _technicals(quote: dict, fundamentals: dict) -> dict:
        """
        Rule-based technical signals derived from available data.
        A full implementation would use historical OHLCV data.
        """
        price     = quote.get("price", 0)
        w52_high  = quote.get("week_52_high", price)
        w52_low   = quote.get("week_52_low",  price)
        change_pct = quote.get("change_pct", 0)

        # RSI approximation (simplified — real RSI needs 14-day OHLCV)
        range_52 = w52_high - w52_low if w52_high > w52_low else 1
        pos_in_range = (price - w52_low) / range_52  # 0 to 1
        rsi = round(30 + pos_in_range * 40)  # Simplified 30–70 range

        if rsi > 70:
            rsi_signal = "Overbought"
        elif rsi < 30:
            rsi_signal = "Oversold"
        else:
            rsi_signal = "Neutral"

        # MACD signal (simplified from momentum)
        macd = "Bullish" if change_pct > 0 else "Bearish"

        # MA signals (approximated from 52W range)
        ma50_above  = price > (w52_low + (range_52 * 0.35))
        ma200_above = price > (w52_low + (range_52 * 0.20))

        momentum = "Strong" if change_pct > 2 else \
                   "Moderate" if change_pct > 0 else \
                   "Weak" if change_pct > -2 else "Negative"

        return {
            "rsi":        rsi,
            "rsi_signal": rsi_signal,
            "macd":       macd,
            "ma50":       "Above" if ma50_above else "Below",
            "ma200":      "Above" if ma200_above else "Below",
            "momentum":   momentum,
        }

    @staticmethod
    def _verdict(fundamentals: dict, technicals: dict) -> str:
        """
        Rule-based buy/hold/sell verdict combining fundamentals + technicals.
        """
        score = 0

        # Fundamental scoring
        pe = fundamentals.get("pe_ratio", 0)
        if 0 < pe < 20:   score += 2
        elif 20 <= pe < 35: score += 1
        elif pe >= 35:    score -= 1

        roe = fundamentals.get("roe", 0)
        if roe > 20:   score += 2
        elif roe > 12: score += 1
        elif roe < 5:  score -= 1

        de = fundamentals.get("debt_to_equity", 0)
        if de < 0.3:    score += 1
        elif de > 1.5:  score -= 2

        rev_growth = fundamentals.get("revenue_growth", 0)
        if rev_growth > 15:  score += 2
        elif rev_growth > 8: score += 1
        elif rev_growth < 0: score -= 1

        # Technical scoring
        if technicals.get("macd") == "Bullish":    score += 1
        if technicals.get("ma50")  == "Above":     score += 1
        if technicals.get("ma200") == "Above":     score += 1
        if technicals.get("rsi_signal") == "Oversold":   score += 1
        if technicals.get("rsi_signal") == "Overbought": score -= 1
        if technicals.get("momentum") == "Strong":  score += 1
        if technicals.get("momentum") == "Negative": score -= 1

        if score >= 6:   return "STRONG BUY"
        elif score >= 3: return "BUY"
        elif score >= 0: return "HOLD"
        elif score >= -3: return "SELL"
        else:            return "STRONG SELL"

    @staticmethod
    async def _ai_summary(symbol: str, quote: dict, fundamentals: dict,
                           technicals: dict, verdict: str) -> str:
        """
        Generates AI narrative summary.
        Uses OpenAI/Claude if API key configured, else rule-based fallback.
        """
        # Rule-based fallback (always available)
        pe     = fundamentals.get("pe_ratio", 0)
        roe    = fundamentals.get("roe", 0)
        de     = fundamentals.get("debt_to_equity", 0)
        rev_g  = fundamentals.get("revenue_growth", 0)
        profit = fundamentals.get("profit_margin", 0)
        price  = quote.get("price", 0)
        w52h   = quote.get("week_52_high", 0)
        w52l   = quote.get("week_52_low",  0)

        from_high = round(((w52h - price) / w52h) * 100, 1) if w52h else 0
        from_low  = round(((price - w52l) / w52l) * 100, 1) if w52l else 0

        valuation = (
            "undervalued relative to peers" if pe and pe < 15 else
            "fairly valued" if pe and pe < 30 else
            "trading at a premium" if pe else "valuation data unavailable"
        )

        roe_comment = (
            "excellent return on equity, indicating efficient use of capital" if roe > 20 else
            "decent return on equity" if roe > 12 else
            "below-average return on equity" if roe else ""
        )

        debt_comment = (
            "virtually debt-free balance sheet" if de < 0.2 else
            "manageable debt levels" if de < 0.8 else
            "elevated debt levels that warrant caution" if de < 1.5 else
            "high debt burden — monitor closely"
        )

        verdict_comment = {
            "STRONG BUY": "Strong fundamentals combined with positive momentum make this a compelling investment opportunity.",
            "BUY":        "Solid fundamentals with positive technical outlook. Consider accumulating on dips.",
            "HOLD":       "Current holders may stay invested. New buyers should wait for a better entry point.",
            "SELL":       "Weakening fundamentals or overvaluation suggest reducing exposure.",
            "STRONG SELL": "Multiple red flags in fundamentals and technicals. Consider exiting positions."
        }.get(verdict, "")

        summary = (
            f"{symbol} is currently {valuation}, trading {from_low:.1f}% above its 52-week low "
            f"and {from_high:.1f}% below its 52-week high. "
        )
        if roe_comment:
            summary += f"The company shows {roe_comment}. "
        summary += f"The balance sheet reflects {debt_comment}. "
        if rev_g:
            summary += f"Revenue growth stands at {rev_g:.1f}%, "
            summary += "indicating healthy top-line expansion. " if rev_g > 10 else "showing moderate growth. "
        summary += f"{verdict_comment} "
        summary += "Note: This analysis is for educational purposes only and is not SEBI-registered investment advice."

        # Optional: Use Claude/OpenAI for richer summary
        if settings.ANTHROPIC_API_KEY:
            try:
                summary = await StockAnalysisEngine._claude_summary(
                    symbol, quote, fundamentals, technicals, verdict
                )
            except Exception as e:
                logger.warning(f"Claude summary failed, using fallback: {e}")

        return summary

    @staticmethod
    async def _claude_summary(symbol, quote, fundamentals, technicals, verdict) -> str:
        """Optional: Claude API for enriched narrative."""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""You are a financial analyst. Write a 3-4 sentence investment analysis for {symbol}.

Data:
- Price: ₹{quote.get('price')} | Change: {quote.get('change_pct')}%
- P/E: {fundamentals.get('pe_ratio')} | ROE: {fundamentals.get('roe')}% | D/E: {fundamentals.get('debt_to_equity')}
- Revenue Growth: {fundamentals.get('revenue_growth')}% | Profit Margin: {fundamentals.get('profit_margin')}%
- RSI: {technicals.get('rsi')} ({technicals.get('rsi_signal')}) | MACD: {technicals.get('macd')}
- 52W: ₹{quote.get('week_52_low')} - ₹{quote.get('week_52_high')}
- Verdict: {verdict}

Rules:
- Be factual and concise
- End with: "Not SEBI-registered investment advice."
- Do not recommend specific investment amounts"""

        msg = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
