"""
engines/retirement_calculator.py — Retirement Planner Engine (BASIC+)
Corpus calculation, SIP requirement, inflation adjustment, milestones
"""

import math
from datetime import datetime


class RetirementEngine:

    @staticmethod
    def calculate(params: dict) -> dict:
        """
        Full retirement corpus calculation.

        Step 1: Inflation-adjust monthly expenses to retirement date
        Step 2: Calculate corpus needed (PV of annuity for retirement years)
        Step 3: Calculate SIP needed to reach corpus
        Step 4: Factor in existing savings
        """
        current_age   = int(params["current_age"])
        retire_age    = int(params["retire_age"])
        life_exp      = int(params.get("life_expectancy", 85))
        monthly_exp   = float(params["monthly_expenses"])
        inflation     = float(params.get("inflation", 6.0)) / 100
        curr_savings  = float(params.get("current_savings", 0))
        return_pre    = float(params.get("return_pre",  12.0)) / 100
        return_post   = float(params.get("return_post",  7.0)) / 100

        # Validation
        if retire_age <= current_age:
            raise ValueError("Retirement age must be greater than current age")
        if life_exp <= retire_age:
            raise ValueError("Life expectancy must be greater than retirement age")

        years_to_retire   = retire_age    - current_age
        retirement_years  = life_exp      - retire_age
        months_to_retire  = years_to_retire  * 12
        months_in_retire  = retirement_years * 12

        # ── Step 1: Inflation-adjusted monthly expense at retirement ──
        monthly_at_retire = monthly_exp * math.pow(1 + inflation, years_to_retire)

        # ── Step 2: Corpus needed (PV of annuity) ─────────────────────
        r_post = return_post / 12
        if r_post > 0:
            corpus = monthly_at_retire * (
                (1 - math.pow(1 + r_post, -months_in_retire)) / r_post
            )
        else:
            corpus = monthly_at_retire * months_in_retire

        # ── Step 3: Future value of current savings ────────────────────
        future_savings = curr_savings * math.pow(1 + return_pre, years_to_retire)
        remaining      = max(0, corpus - future_savings)

        # ── Step 4: SIP needed ─────────────────────────────────────────
        r_pre = return_pre / 12
        if remaining > 0 and r_pre > 0 and months_to_retire > 0:
            sip = (remaining * r_pre) / (
                (math.pow(1 + r_pre, months_to_retire) - 1) * (1 + r_pre)
            )
        elif remaining > 0:
            sip = remaining / months_to_retire
        else:
            sip = 0

        sip = math.ceil(sip)

        # ── Milestone projections ──────────────────────────────────────
        milestones = RetirementEngine._milestones(
            sip=sip, r=r_pre, months=months_to_retire,
            init=curr_savings, corpus=corpus,
            current_age=current_age
        )

        # ── Retirement income analysis ─────────────────────────────────
        monthly_income = monthly_at_retire
        sustainable_withdrawal_rate = return_post - inflation * 100 / 100  # real return

        return {
            "corpus_needed":           round(corpus),
            "monthly_sip":             sip,
            "years_to_retire":         years_to_retire,
            "months_to_retire":        months_to_retire,
            "retirement_years":        retirement_years,
            "monthly_expense_today":   round(monthly_exp),
            "monthly_expense_retire":  round(monthly_at_retire),
            "future_savings":          round(future_savings),
            "remaining_corpus":        round(remaining),
            "total_sip_invested":      round(sip * months_to_retire),
            "milestones":              milestones,
            "inflation_used":          inflation * 100,
            "return_pre_used":         return_pre  * 100,
            "return_post_used":        return_post * 100,
            "retirement_income_monthly": round(monthly_income),
            "note": (
                f"At {inflation*100:.0f}% inflation, ₹{monthly_exp:,.0f}/month today "
                f"= ₹{monthly_at_retire:,.0f}/month at retirement."
            )
        }

    @staticmethod
    def _milestones(sip, r, months, init, corpus, current_age):
        milestones = []
        checkpoints = [0.25, 0.5, 0.75, 1.0]
        labels = [
            "25% Milestone",
            "Halfway Point 🏁",
            "75% Achieved",
            "Retirement Day! 🎉"
        ]
        for pct, label in zip(checkpoints, labels):
            m = max(1, int(months * pct))
            if r > 0:
                fv = sip * ((math.pow(1+r, m) - 1) / r) * (1+r) + \
                     init * math.pow(1+r, m)
            else:
                fv = sip * m + init
            milestones.append({
                "age":    current_age + round(m / 12),
                "month":  m,
                "label":  label,
                "amount": round(fv),
                "pct_of_corpus": round((fv / corpus) * 100) if corpus > 0 else 0,
            })
        return milestones
