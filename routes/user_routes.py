"""
routes/user_routes.py — /api/v1/user/*
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from services.auth_service import AuthService
from firebase.firebase_service import PlanService
from middleware.access_middleware import get_current_user

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    name:       Optional[str] = None
    phone:      Optional[str] = None
    city:       Optional[str] = None
    occupation: Optional[str] = None
    income:     Optional[str] = None


# GET /api/v1/user/profile
@router.get("/profile")
async def get_profile(request: Request):
    uid = request.state.uid
    try:
        return AuthService.get_user_profile(uid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# PUT /api/v1/user/profile
@router.put("/profile")
async def update_profile(body: UpdateProfileRequest, request: Request):
    uid = request.state.uid
    updated = AuthService.update_profile(uid, body.model_dump(exclude_none=True))
    return updated


# GET /api/v1/user/plan
@router.get("/plan")
async def get_plan(request: Request):
    uid = request.state.uid
    return PlanService.get_user_plan(uid)
