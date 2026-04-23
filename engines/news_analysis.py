"""
engines/news_analysis.py — News Analysis Engine (FREE)
Fetches financial news from NewsAPI + categorizes + sentiment analysis
"""

import httpx
from datetime import datetime, timedelta
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache (15 min TTL)
_news_cache: dict = {}

NEWS_SOURCES = [
    "the-times-of-india",
    "the-hindu",
    "economic-times",
    "business-standard",
    "livemint",
    "moneycontrol",
]

CATEGORY_KEYWORDS = {
    "market":       ["nifty", "sensex", "bse", "nse", "market", "index", "rally", "fall"],
    "stocks":       ["stock", "share", "equity", "ipo", "listing", "buyback", "dividend", "quarterly"],
    "mutual-funds": ["mutual fund", "sip", "nav", "aum", "scheme", "folio", "elss", "nfo"],
    "economy":      ["rbi", "gdp", "inflation", "repo rate", "budget", "fiscal", "cpi", "wpi", "rbi policy"],
    "global":       ["fed", "us market", "china", "global", "dollar", "oil", "crude", "opec", "forex"],
}

POSITIVE_WORDS = {"rally", "surge", "gain", "rise", "record", "high", "profit", "growth",
                   "bullish", "positive", "strong", "beat", "upgrade", "buy"}
NEGATIVE_WORDS = {"fall", "drop", "decline", "crash", "loss", "bearish", "weak", "sell",
                   "concern", "risk", "fear", "cut", "downgrade", "miss", "debt"}


class NewsEngine:

    @staticmethod
    async def get_curated_news(category: str = "all") -> dict:
        """
        Fetch, categorize, and return financial news.
        Uses NewsAPI if key configured, else demo data.
        """
        cache_key = f"news:{category}"
        if cache_key in _news_cache:
            entry = _news_cache[cache_key]
            if datetime.utcnow() < entry["expires"]:
                return entry["data"]

        if settings.NEWS_API_KEY and settings.NEWS_API_KEY != "your-newsapi-key":
            try:
                articles = await NewsEngine._fetch_newsapi(category)
            except Exception as e:
                logger.warning(f"NewsAPI failed: {e}. Using demo data.")
                articles = NewsEngine._demo_news()
        else:
            articles = NewsEngine._demo_news()

        # Filter by category
        if category != "all":
            articles = [a for a in articles if a.get("category") == category]

        result = {"news": articles, "count": len(articles), "category": category,
                  "fetched_at": datetime.utcnow().isoformat()}

        _news_cache[cache_key] = {
            "data":    result,
            "expires": datetime.utcnow() + timedelta(minutes=15),
        }
        return result

    @staticmethod
    async def _fetch_newsapi(category: str) -> list:
        queries = {
            "all":          "India stock market finance investment",
            "market":       "Nifty Sensex BSE NSE market",
            "stocks":       "India stocks equity NSE BSE earnings",
            "mutual-funds": "mutual fund SIP NAV India",
            "economy":      "RBI India GDP inflation budget",
            "global":       "global market Fed dollar oil India impact",
        }
        query = queries.get(category, queries["all"])

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "language": "en",
                    "sortBy":   "publishedAt",
                    "pageSize": 20,
                    "from":     (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "apiKey":   settings.NEWS_API_KEY,
                }
            )
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for a in data.get("articles", []):
            if not a.get("title") or a["title"] == "[Removed]":
                continue
            articles.append({
                "title":      a["title"],
                "summary":    a.get("description", "")[:200],
                "url":        a.get("url", "#"),
                "source":     a.get("source", {}).get("name", "News"),
                "time_ago":   NewsEngine._time_ago(a.get("publishedAt", "")),
                "category":   NewsEngine._categorize(a.get("title", "") + " " + a.get("description", "")),
                "sentiment":  NewsEngine._sentiment(a.get("title", "") + " " + a.get("description", "")),
            })

        return articles

    @staticmethod
    def _categorize(text: str) -> str:
        text_lower = text.lower()
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        return "market"

    @staticmethod
    def _sentiment(text: str) -> str:
        text_lower = text.lower()
        pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
        neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
        if pos > neg:   return "positive"
        elif neg > pos: return "negative"
        return "neutral"

    @staticmethod
    def _time_ago(dt_str: str) -> str:
        try:
            dt   = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            diff = datetime.now(dt.tzinfo) - dt
            mins = int(diff.total_seconds() / 60)
            if mins < 60:     return f"{mins}m ago"
            elif mins < 1440: return f"{mins//60}h ago"
            else:             return f"{mins//1440}d ago"
        except Exception:
            return "Recently"

    @staticmethod
    def _demo_news() -> list:
        """Fallback demo news when NewsAPI is not configured."""
        return [
            {"title": "RBI Keeps Repo Rate Unchanged at 6.5% in Latest MPC Meeting",
             "summary": "The Monetary Policy Committee voted unanimously to hold rates, citing balanced inflation risks and supporting economic growth momentum.",
             "url": "#", "source": "Economic Times", "time_ago": "1h ago",
             "category": "economy", "sentiment": "positive"},

            {"title": "Nifty 50 Hits New High as FII Buying Returns in Large Cap Stocks",
             "summary": "Foreign institutional investors turned net buyers after three weeks of selling, injecting ₹4,200 crore into Indian equities.",
             "url": "#", "source": "Business Standard", "time_ago": "2h ago",
             "category": "market", "sentiment": "positive"},

            {"title": "TCS Reports Strong Q3 Results — Revenue Up 8.2% YoY",
             "summary": "Tata Consultancy Services beat analyst estimates with deal wins across BFSI and healthcare verticals.",
             "url": "#", "source": "Mint", "time_ago": "4h ago",
             "category": "stocks", "sentiment": "positive"},

            {"title": "SEBI Proposes Stricter Norms for Equity Mutual Fund Categorization",
             "summary": "The market regulator has proposed reclassifying mid and small cap fund exposure limits to better protect retail investors.",
             "url": "#", "source": "SEBI", "time_ago": "5h ago",
             "category": "mutual-funds", "sentiment": "neutral"},

            {"title": "US Fed Signals Possible Rate Cut in Second Half of 2025",
             "summary": "Federal Reserve minutes indicate policymakers are watching inflation data closely before committing to easing.",
             "url": "#", "source": "Bloomberg", "time_ago": "6h ago",
             "category": "global", "sentiment": "positive"},

            {"title": "India's CPI Inflation Drops to 4.8% — Lowest in 6 Months",
             "summary": "Consumer price inflation eased on falling vegetable prices, coming within RBI's comfort zone.",
             "url": "#", "source": "MoSPI", "time_ago": "8h ago",
             "category": "economy", "sentiment": "positive"},

            {"title": "Gold Prices Hit ₹73,400/10g as Geopolitical Tensions Rise",
             "summary": "Safe-haven demand drove gold to fresh highs in domestic markets.",
             "url": "#", "source": "CNBC TV18", "time_ago": "10h ago",
             "category": "market", "sentiment": "positive"},

            {"title": "Smallcap Index Underperforms — Mutual Fund Managers Turn Cautious",
             "summary": "Several fund houses have been reducing small cap exposure after valuations stretched above 5-year averages.",
             "url": "#", "source": "Moneycontrol", "time_ago": "12h ago",
             "category": "mutual-funds", "sentiment": "negative"},
        ]
