"""
routes/subscription_routes.py — /api/v1/payment/*
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.payment_service import CashfreeService
from services.subscription_service import SubscriptionService

router = APIRouter()


class CreateOrderRequest(BaseModel):
    plan_id:  str
    amount:   float
    currency: str = "INR"


class VerifyPaymentRequest(BaseModel):
    order_id:   str
    plan_id:    str
    payment_id: Optional[str] = ""
    signature:  Optional[str] = ""


# POST /api/v1/payment/create-order
@router.post("/create-order")
async def create_order(body: CreateOrderRequest, request: Request):
    uid = request.state.uid
    try:
        result = await CashfreeService.create_order(uid=uid, plan_id=body.plan_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")


# POST /api/v1/payment/verify
@router.post("/verify")
async def verify_payment(body: VerifyPaymentRequest, request: Request):
    uid = request.state.uid
    try:
        result = await CashfreeService.verify_payment(
            uid=uid,
            order_id=body.order_id,
            plan_id=body.plan_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


# POST /api/v1/payment/webhook  (Cashfree server callback — NO auth header)
@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Cashfree webhook — called by Cashfree servers after payment.
    Verify using Cashfree signature before processing.
    """
    try:
        payload = await request.json()
        result  = await CashfreeService.handle_webhook(payload)
        return result
    except Exception as e:
        # Always return 200 to Cashfree to prevent retries on our error
        return {"status": "error", "detail": str(e)}


# GET /api/v1/payment/history
@router.get("/history")
async def payment_history(request: Request):
    uid = request.state.uid
    return SubscriptionService.get_payment_history(uid)
