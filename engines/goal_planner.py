"""
engines/goal_planner.py — Goal Planner Engine (BASIC+)
SIP calculator with future value projections and savings gap analysis
"""

from firebase_admin import firestore
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math
import logging

logger = logging.getLogger(__name__)

GOAL_ICONS = {
    "home":      "🏠",
    "car":       "🚗",
    "education": "🎓",
    "wedding":   "💍",
    "travel":    "✈️",
    "emergency": "🛡️",
    "business":  "💼",
    "custom":    "🎯",
}


class GoalPlannerEngine:

    @staticmethod
    def calculate(uid: str, params: dict) -> dict:
        """
        Core SIP calculation using Future Value of Annuity formula.

        FV = P * [((1+r)^n - 1) / r] * (1+r)
        Solving for P (monthly SIP):
        P = FV * r / [((1+r)^n - 1) * (1+r)]
        """
        goal_type     = params.get("goal_type", "custom")
        goal_name     = params.get("goal_name", "My Goal")
        target_amount = float(params.get("target_amount", 0))
        target_date   = params.get("target_date", "")
        current_saved = float(params.get("current_saved", 0))
        annual_return = float(params.get("annual_return", 12.0))

        if target_amount <= 0:
            raise ValueError("Target amount must be positive")

        # Parse months
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m")
            now       = datetime.utcnow().replace(day=1)
            rd        = relativedelta(target_dt, now)
            months    = max(1, rd.months + rd.years * 12)
        except Exception:
            raise ValueError("Invalid target_date. Use format: YYYY-MM")

        r   = annual_return / 100 / 12          # monthly rate
        fv  = target_amount - current_saved      # remaining amount needed

        if fv <= 0:
            # Already have enough!
            return {
                "sip_required":  0,
                "months":        months,
                "goal_name":     goal_name,
                "goal_icon":     GOAL_ICONS.get(goal_type, "🎯"),
                "target_amount": target_amount,
                "current_saved": current_saved,
                "total_invested": 0,
                "returns_earned": 0,
                "progress_pct":  100,
                "message":       "You already have enough saved for this goal! 🎉",
                "milestones":    [],
            }

        # SIP formula
        if r == 0:
            sip = fv / months
        else:
            sip = (fv * r) / ((math.pow(1 + r, months) - 1) * (1 + r))

        sip           = math.ceil(sip)
        total_invested = sip * months
        returns_earned = max(0, fv - total_invested)
        progress_pct  = min(100, round((current_saved / target_amount) * 100))

        # Lumpsum alternative
        if r > 0:
            lumpsum = fv / math.pow(1 + r, months)
        else:
            lumpsum = fv

        # Year-wise milestones
        milestones = GoalPlannerEngine._build_milestones(
            sip, r, months, current_saved, target_amount
        )

        result = {
            "goal_name":      goal_name,
            "goal_type":      goal_type,
            "goal_icon":      GOAL_ICONS.get(goal_type, "🎯"),
            "target_amount":  target_amount,
            "current_saved":  current_saved,
            "months":         months,
            "years":          round(months / 12, 1),
            "annual_return":  annual_return,
            "sip_required":   sip,
            "lumpsum_needed": round(lumpsum),
            "total_invested": round(total_invested),
            "returns_earned": round(returns_earned),
            "progress_pct":   progress_pct,
            "milestones":     milestones,
        }

        # Save to Firestore
        GoalPlannerEngine._save(uid, result)
        return result

    @staticmethod
    def _build_milestones(sip: float, r: float, total_months: int,
                           initial: float, target: float) -> list:
        milestones = []
        checkpoints = [
            int(total_months * 0.25),
            int(total_months * 0.5),
            int(total_months * 0.75),
            total_months,
        ]
        labels = ["25% Mark", "Halfway", "75% Done", "Goal Achieved! 🎉"]

        for months, label in zip(checkpoints, labels):
            if months == 0:
                continue
            if r > 0:
                fv = sip * ((math.pow(1 + r, months) - 1) / r) * (1 + r) + \
                     initial * math.pow(1 + r, months)
            else:
                fv = sip * months + initial
            milestones.append({
                "month":  months,
                "label":  label,
                "amount": round(fv),
                "pct":    round((fv / target) * 100),
            })

        return milestones

    @staticmethod
    def _save(uid: str, result: dict):
        try:
            db = firestore.client()
            db.collection("users").document(uid)\
              .collection("goals")\
              .add({**result, "created_at": datetime.utcnow()})
        except Exception as e:
            logger.warning(f"Could not save goal for {uid}: {e}")
