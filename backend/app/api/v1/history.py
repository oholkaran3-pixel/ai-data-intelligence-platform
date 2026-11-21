from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.models import ActivityHistory, User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/history", tags=["User Activity History"])

@router.get("")
def get_user_history(
    activity_type: Optional[str] = Query(None),
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(ActivityHistory).filter(ActivityHistory.user_id == current_user.id)
    if activity_type:
        query = query.filter(ActivityHistory.activity_type == activity_type)
        
    records = query.order_by(ActivityHistory.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "activity_type": r.activity_type,
            "description": r.description,
            "project_id": r.project_id,
            "status": r.status,
            "resource_id": r.resource_id,
            "created_at": r.created_at
        }
        for r in records
    ]
