from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, Project, Dataset, Report, ActivityHistory
from app.core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

@router.get("/metrics")
def get_admin_metrics(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_projects = db.query(Project).count()
    total_datasets = db.query(Dataset).count()
    total_reports = db.query(Report).count()
    recent_activities = db.query(ActivityHistory).order_by(ActivityHistory.created_at.desc()).limit(20).all()

    return {
        "platform_status": "Operational",
        "total_users": total_users,
        "active_users": active_users,
        "total_projects": total_projects,
        "total_datasets": total_datasets,
        "total_reports_generated": total_reports,
        "recent_system_activities": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "type": a.activity_type,
                "description": a.description,
                "timestamp": a.created_at
            }
            for a in recent_activities
        ]
    }
