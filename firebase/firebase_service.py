"""
firebase/firebase_service.py — Firestore database operations
All user data, plans, and payment records stored here
"""

from firebase_admin import firestore
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def _db():
    """Get Firestore client."""
    return firestore.client()


# ════════════════════════════════════════════════════════════
# USER OPERATIONS
# ════════════════════════════════════════════════════════════

class FirebaseService:

    # ── Get or Create User ────────────────────────────────
    @staticmethod
    def get_user(uid: str) -> Optional[dict]:
        doc = _db().collection("users").document(uid).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def create_or_update_user(uid: str, data: dict) -> dict:
        """Upsert user document. Called on login/signup sync."""
        ref = _db().collection("users").document(uid)
        doc = ref.get()

        if doc.exists:
            # Update only provided fields
            update_data = {k: v for k, v in data.items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            ref.update(update_data)
        else:
            # Create new user
            new_user = {
                "uid":        uid,
                "email":      data.get("email", ""),
                "name":       data.get("name", ""),
                "photo":      data.get("photo", ""),
                "plan":       "free",
                "plan_expiry": None,
                "plan_name":  "Free",
                "is_active":  True,
                "is_admin":   False,
                "login_count": 0,
                "total_revenue": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            ref.set(new_user)

        # Increment login count
        ref.update({"login_count": firestore.Increment(1)})

        return ref.get().to_dict()

    @staticmethod
    def update_user_profile(uid: str, data: dict):
        allowed = ["name", "phone", "city", "occupation", "income", "photo"]
        update  = {k: v for k, v in data.items() if k in allowed and v is not None}
        update["updated_at"] = datetime.utcnow()
        _db().collection("users").document(uid).update(update)

    @staticmethod
    def get_all_users(limit: int = 50, offset: int = 0,
                      search: str = "", plan_filter: str = "") -> dict:
        ref = _db().collection("users")
        query = ref.order_by("created_at", direction=firestore.Query.DESCENDING)

        if plan_filter:
            query = query.where("plan", "==", plan_filter)

        docs  = query.limit(limit).stream()
        users = []
        for doc in docs:
            d = doc.to_dict()
            # Client-side search filter (Firestore doesn't support LIKE)
            if search:
                s = search.lower()
                if s not in (d.get("email","") + d.get("name","")).lower():
                    continue
            users.append(d)

        # Total count
        total_ref = _db().collection("users")
        if plan_filter:
            total_ref = total_ref.where("plan", "==", plan_filter)
        total = len(list(total_ref.stream()))

        return {"users": users, "total": total}

    @staticmethod
    def delete_user(uid: str):
        _db().collection("users").document(uid).delete()
        # Also delete their payments
        payments = _db().collection("payments").where("uid", "==", uid).stream()
        for p in payments:
            p.reference.delete()
        logger.info(f"Deleted user and payments for uid: {uid}")


    # ── Admin check ───────────────────────────────────────
    @staticmethod
    def is_admin(uid: str) -> bool:
        user = FirebaseService.get_user(uid)
        return bool(user and user.get("is_admin", False))


# ════════════════════════════════════════════════════════════
# PLAN / SUBSCRIPTION OPERATIONS
# ════════════════════════════════════════════════════════════

class PlanService:

    @staticmethod
    def get_user_plan(uid: str) -> dict:
        user = FirebaseService.get_user(uid)
        if not user:
            return {"plan_id": "free", "plan_name": "Free", "expiry_date": None}

        plan       = user.get("plan", "free")
        expiry     = user.get("plan_expiry")
        plan_name  = user.get("plan_name", "Free")

        # Auto-downgrade if expired
        if expiry and datetime.utcnow() > expiry:
            PlanService.expire_plan(uid)
            return {"plan_id": "free", "plan_name": "Free", "expiry_date": None}

        return {
            "plan_id":     plan,
            "plan_name":   plan_name,
            "expiry_date": expiry.isoformat() if expiry else None,
        }

    @staticmethod
    def activate_plan(uid: str, plan_id: str, duration_days: int,
                      order_id: str, amount: int):
        """Activate or extend a user's plan after successful payment."""
        plan_names = {
            "basic":        "Basic Plan",
            "pro":          "Pro Plan",
            "elite":        "Elite Plan",
            "basic_yearly": "Basic Plan (Yearly)",
            "pro_yearly":   "Pro Plan (Yearly)",
        }
        # Strip _yearly suffix for access control
        base_plan = plan_id.replace("_yearly", "")
        expiry    = datetime.utcnow() + timedelta(days=duration_days)

        _db().collection("users").document(uid).update({
            "plan":        base_plan,
            "plan_name":   plan_names.get(plan_id, plan_id),
            "plan_expiry": expiry,
            "updated_at":  datetime.utcnow(),
        })
        logger.info(f"Plan activated: uid={uid} plan={plan_id} expiry={expiry}")
        return expiry.isoformat()

    @staticmethod
    def expire_plan(uid: str):
        _db().collection("users").document(uid).update({
            "plan":        "free",
            "plan_name":   "Free",
            "plan_expiry": None,
            "updated_at":  datetime.utcnow(),
        })

    @staticmethod
    def get_plan_stats() -> dict:
        users = list(_db().collection("users").stream())
        stats = {"free": 0, "basic": 0, "pro": 0, "elite": 0}
        for u in users:
            d    = u.to_dict()
            plan = d.get("plan", "free")
            if plan in stats:
                stats[plan] += 1
        return stats


# ════════════════════════════════════════════════════════════
# PAYMENT OPERATIONS
# ════════════════════════════════════════════════════════════

class PaymentService:

    @staticmethod
    def create_payment_record(uid: str, order_id: str, plan_id: str,
                               amount: int) -> str:
        ref = _db().collection("payments").document(order_id)
        ref.set({
            "order_id":   order_id,
            "uid":        uid,
            "plan":       plan_id,
            "amount":     amount,
            "status":     "PENDING",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        return order_id

    @staticmethod
    def update_payment_status(order_id: str, status: str,
                               payment_id: str = "", user_email: str = ""):
        _db().collection("payments").document(order_id).update({
            "status":      status,
            "payment_id":  payment_id,
            "user_email":  user_email,
            "updated_at":  datetime.utcnow(),
        })

        # Update user's total revenue on success
        if status == "SUCCESS":
            doc   = _db().collection("payments").document(order_id).get().to_dict()
            uid   = doc.get("uid")
            amount = doc.get("amount", 0)
            if uid:
                _db().collection("users").document(uid).update({
                    "total_revenue": firestore.Increment(amount)
                })

    @staticmethod
    def get_payment(order_id: str) -> Optional[dict]:
        doc = _db().collection("payments").document(order_id).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def get_user_payments(uid: str) -> list:
        docs = (_db().collection("payments")
                .where("uid", "==", uid)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(20)
                .stream())
        return [d.to_dict() for d in docs]

    @staticmethod
    def get_all_payments(limit: int = 50, status_filter: str = "",
                          plan_filter: str = "") -> dict:
        ref = _db().collection("payments").order_by(
            "created_at", direction=firestore.Query.DESCENDING)
        if status_filter:
            ref = ref.where("status", "==", status_filter)
        if plan_filter:
            ref = ref.where("plan", "==", plan_filter)

        docs     = ref.limit(limit).stream()
        payments = [d.to_dict() for d in docs]

        # Revenue stats
        all_success = list(
            _db().collection("payments").where("status", "==", "SUCCESS").stream()
        )
        total_revenue = sum(d.to_dict().get("amount", 0) for d in all_success)

        # Month revenue
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        month_rev   = sum(
            d.to_dict().get("amount", 0)
            for d in all_success
            if d.to_dict().get("created_at", datetime.min) >= month_start
        )

        total_tx      = len(list(_db().collection("payments").stream()))
        success_count = len(all_success)
        success_rate  = round(success_count / total_tx * 100, 1) if total_tx else 0

        return {
            "payments": payments,
            "stats": {
                "total_revenue":    total_revenue,
                "month_revenue":    month_rev,
                "success_rate":     success_rate,
                "total_transactions": total_tx,
            }
        }


# ════════════════════════════════════════════════════════════
# ADMIN STATS
# ════════════════════════════════════════════════════════════

class AdminService:

    @staticmethod
    def get_dashboard_stats() -> dict:
        users    = list(_db().collection("users").stream())
        payments = list(_db().collection("payments")
                        .where("status", "==", "SUCCESS").stream())

        total_users = len(users)
        active_subs = sum(
            1 for u in users
            if u.to_dict().get("plan", "free") != "free"
        )

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        new_today   = sum(
            1 for u in users
            if u.to_dict().get("created_at", datetime.min) >= today_start
        )
        payments_today = [
            p.to_dict() for p in payments
            if p.to_dict().get("created_at", datetime.min) >= today_start
        ]

        total_revenue   = sum(p.to_dict().get("amount", 0) for p in payments)
        revenue_today   = sum(p.get("amount", 0) for p in payments_today)

        plan_stats = PlanService.get_plan_stats()

        return {
            "total_users":     total_users,
            "active_subs":     active_subs,
            "new_users_today": new_today,
            "mrr":             active_subs * 999,   # Approx
            "mrr_growth":      0,
            "churn_rate":      0,
            "payments_today":  len(payments_today),
            "revenue_today":   revenue_today,
            "total_revenue":   total_revenue,
            **plan_stats,
        }
