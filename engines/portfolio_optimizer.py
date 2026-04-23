"""
engines/portfolio_optimizer.py — Portfolio Optimizer Engine (PRO)
Modern Portfolio Theory based allocation with specific fund recommendations
"""

import math


# ── Portfolio templates by risk profile ──────────────────
PORTFOLIOS = {
    "conservative": {
        "label":        "Conservative Portfolio",
        "cagr":         8.0,
        "risk_level":   "Low",
        "max_drawdown": "5-8%",
        "allocation": [
            {"asset": "Debt Mutual Funds",       "category": "Debt",      "pct": 40, "color": "#3B82F6", "expected_return": "7-8%",  "examples": ["HDFC Short Term Debt Fund", "ICICI Pru Corporate Bond"]},
            {"asset": "Fixed Deposits / Bonds",  "category": "Debt",      "pct": 25, "color": "#06B6D4", "expected_return": "6-7%",  "examples": ["SBI FD (5yr)", "RBI Floating Rate Bonds"]},
            {"asset": "Gold ETF / SGB",          "category": "Commodity", "pct": 20, "color": "#C9A84C", "expected_return": "8-10%", "examples": ["Nippon India Gold ETF", "SGB 2024"]},
            {"asset": "Large Cap Equity MF",     "category": "Equity",    "pct": 15, "color": "#22C55E", "expected_return": "10-12%","examples": ["Mirae Asset Large Cap", "Axis Bluechip Fund"]},
        ],
    },
    "moderate": {
        "label":        "Balanced Portfolio",
        "cagr":         11.0,
        "risk_level":   "Medium",
        "max_drawdown": "15-20%",
        "allocation": [
            {"asset": "Large Cap Equity MF",  "category": "Equity",    "pct": 35, "color": "#22C55E", "expected_return": "10-12%", "examples": ["Mirae Asset Large Cap", "UTI Nifty 50 Index Fund"]},
            {"asset": "Debt / Hybrid Fund",   "category": "Hybrid",    "pct": 25, "color": "#3B82F6", "expected_return": "8-9%",   "examples": ["HDFC Balanced Advantage", "SBI Equity Hybrid"]},
            {"asset": "Mid Cap MF",           "category": "Equity",    "pct": 20, "color": "#F59E0B", "expected_return": "12-15%", "examples": ["Kotak Emerging Equity", "Axis Mid Cap Fund"]},
            {"asset": "Gold ETF",             "category": "Commodity", "pct": 10, "color": "#C9A84C", "expected_return": "8-10%",  "examples": ["Nippon India Gold ETF"]},
            {"asset": "International Fund",   "category": "Global",    "pct": 10, "color": "#A78BFA", "expected_return": "10-14%", "examples": ["Motilal Oswal Nasdaq 100", "Parag Parikh Flexi Cap"]},
        ],
    },
    "moderate-aggressive": {
        "label":        "Growth Portfolio",
        "cagr":         13.5,
        "risk_level":   "Moderate-High",
        "max_drawdown": "25-35%",
        "allocation": [
            {"asset": "Large + Mid Cap MF",   "category": "Equity",    "pct": 45, "color": "#22C55E", "expected_return": "12-15%", "examples": ["Mirae Asset Emerging Bluechip", "Canara Robeco Emerging Equities"]},
            {"asset": "Small Cap MF",         "category": "Equity",    "pct": 20, "color": "#F59E0B", "expected_return": "14-18%", "examples": ["Nippon India Small Cap", "SBI Small Cap Fund"]},
            {"asset": "International ETF",    "category": "Global",    "pct": 15, "color": "#A78BFA", "expected_return": "10-14%", "examples": ["Motilal Oswal Nasdaq 100 ETF"]},
            {"asset": "Sector / Thematic MF", "category": "Equity",    "pct": 10, "color": "#EC4899", "expected_return": "12-20%", "examples": ["Mirae Asset Healthcare", "ICICI Pru Technology"]},
            {"asset": "Gold ETF",             "category": "Commodity", "pct": 10, "color": "#C9A84C", "expected_return": "8-10%",  "examples": ["Nippon India Gold ETF"]},
        ],
    },
    "aggressive": {
        "label":        "Aggressive Growth Portfolio",
        "cagr":         16.0,
        "risk_level":   "High",
        "max_drawdown": "40-55%",
        "allocation": [
            {"asset": "Mid + Small Cap MF",    "category": "Equity",    "pct": 40, "color": "#22C55E", "expected_return": "14-20%", "examples": ["Nippon India Small Cap", "Kotak Small Cap Fund"]},
            {"asset": "Direct Stocks (NSE)",   "category": "Equity",    "pct": 25, "color": "#F59E0B", "expected_return": "15-25%", "examples": ["Build your own watchlist", "Focus on quality businesses"]},
            {"asset": "International Equity",  "category": "Global",    "pct": 15, "color": "#A78BFA", "expected_return": "10-15%", "examples": ["Motilal Oswal S&P 500 Index", "NASDAQ 100 ETF"]},
            {"asset": "Thematic / Sector MF",  "category": "Equity",    "pct": 15, "color": "#EC4899", "expected_return": "12-22%", "examples": ["ICICI Pru Technology", "Tata Digital India Fund"]},
            {"asset": "Gold ETF",              "category": "Commodity", "pct": 5,  "color": "#C9A84C", "expected_return": "8-10%",  "examples": ["Nippon India Gold ETF"]},
        ],
    },
}


class PortfolioEngine:

    @staticmethod
    def optimize(amount: float, risk: str, horizon: int) -> dict:
        risk_key = risk.lower().replace(" ", "-")
        p = PORTFOLIOS.get(risk_key, PORTFOLIOS["moderate"])

        # Projected value
        projected = amount * math.pow(1 + p["cagr"] / 100, horizon)

        # Holdings with rupee amounts
        holdings = []
        for asset in p["allocation"]:
            holdings.append({
                **asset,
                "amount": round(amount * asset["pct"] / 100),
            })

        # SIP equivalent (if monthly SIP to reach same amount)
        r    = (p["cagr"] / 100) / 12
        n    = horizon * 12
        if r > 0:
            sip_equiv = (amount * math.pow(1 + r, n) * r) / (math.pow(1 + r, n) - 1)
        else:
            sip_equiv = amount / n

        return {
            "risk_profile":    risk,
            "label":           p["label"],
            "investment":      round(amount),
            "horizon_years":   horizon,
            "expected_cagr":   p["cagr"],
            "projected_value": round(projected),
            "projected_gain":  round(projected - amount),
            "gain_pct":        round(((projected - amount) / amount) * 100, 1),
            "risk_level":      p["risk_level"],
            "max_drawdown":    p["max_drawdown"],
            "allocation":      holdings,
            "monthly_sip_equiv": round(sip_equiv),
            "disclaimer":      (
                "Returns are indicative and based on historical averages. "
                "Actual returns may vary. Not SEBI-registered investment advice."
            ),
        }
