"""
routes/admin_routes.py — /api/v1/admin/*
All routes require admin role
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from middleware.access_middleware import require_admin
from firebase.firebase_service import FirebaseService, AdminService, PlanService, PaymentService

router = APIRouter()


class UpdateUserRequest(BaseModel):
    name:     Optional[str] = None
    plan:     Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class UpdatePlanRequest(BaseModel):
    name:        Optional[str]   = None
    price:       Optional[int]   = None
    yearly_price: Optional[int]  = None
    description: Optional[str]   = None
    is_active:   Optional[bool]  = None


# GET /api/v1/admin/stats
@router.get("/stats", dependencies=[Depends(require_admin)])
async def get_stats():
    return AdminService.get_dashboard_stats()


# GET /api/v1/admin/users
@router.get("/users", dependencies=[Depends(require_admin)])
async def get_users(
    limit:  int = Query(50, le=200),
    page:   int = Query(1, ge=1),
    search: str = Query(""),
    plan:   str = Query(""),
):
    offset = (page - 1) * limit
    return FirebaseService.get_all_users(
        limit=limit, offset=offset,
        search=search, plan_filter=plan
    )


# PUT /api/v1/admin/users/{uid}
@router.put("/users/{uid}", dependencies=[Depends(require_admin)])
async def update_user(uid: str, body: UpdateUserRequest):
    user = FirebaseService.get_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = body.model_dump(exclude_none=True)
    if updates:
        from firebase_admin import firestore
        from datetime import datetime
        updates["updated_at"] = datetime.utcnow()
        firestore.client().collection("users").document(uid).update(updates)

    return {"success": True, "uid": uid}


# DELETE /api/v1/admin/users/{uid}
@router.delete("/users/{uid}", dependencies=[Depends(require_admin)])
async def delete_user(uid: str, request: Request):
    # Prevent self-delete
    if uid == request.state.uid:
        raise HTTPException(status_code=400, detail="Cannot delete your own account.")
    FirebaseService.delete_user(uid)
    return {"success": True, "deleted": uid}


# GET /api/v1/admin/payments
@router.get("/payments", dependencies=[Depends(require_admin)])
async def get_payments(
    limit:  int = Query(50, le=200),
    status: str = Query(""),
    plan:   str = Query(""),
):
    return PaymentService.get_all_payments(
        limit=limit,
        status_filter=status,
        plan_filter=plan
    )


# GET /api/v1/admin/plans
@router.get("/plans", dependencies=[Depends(require_admin)])
async def get_plans():
    stats = PlanService.get_plan_stats()
    plans = [
        {"id": "free",  "name": "Free Plan",  "price": 0,    "is_active": True, "active_subscribers": stats.get("free",  0)},
        {"id": "basic", "name": "Basic Plan", "price": 499,  "is_active": True, "active_subscribers": stats.get("basic", 0)},
        {"id": "pro",   "name": "Pro Plan",   "price": 999,  "is_active": True, "active_subscribers": stats.get("pro",   0)},
        {"id": "elite", "name": "Elite Plan", "price": 1999, "is_active": True, "active_subscribers": stats.get("elite", 0)},
    ]
    return plans


# PUT /api/v1/admin/plans/{plan_id}
@router.put("/plans/{plan_id}", dependencies=[Depends(require_admin)])
async def update_plan(plan_id: str, body: UpdatePlanRequest):
    # In a real app, store plan config in Firestore
    # For now return success (prices managed via config.py)
    return {"success": True, "plan_id": plan_id, "updated": body.model_dump(exclude_none=True)}
