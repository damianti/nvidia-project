from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.config import get_db
from app.database.models import User, Billing, Subscription
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/my-billing")
async def get_my_billing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's billing information"""
    billings = db.query(Billing).filter(Billing.user_id == current_user.id).all()
    subscriptions = db.query(Subscription).filter(Subscription.user_id == current_user.id).all()
    
    return {
        "user_id": current_user.id,
        "billings": billings,
        "subscriptions": subscriptions
    }

@router.get("/my-usage")
async def get_my_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's usage statistics"""
    # This would be implemented with actual usage tracking
    # For now, return mock data
    return {
        "user_id": current_user.id,
        "current_month": {
            "cpu_hours": 24.5,
            "memory_gb_hours": 48.2,
            "storage_gb_hours": 12.8,
            "network_gb": 156.7
        },
        "estimated_cost": 15.75
    }




