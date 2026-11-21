from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User
from app.integrations.powerbi import PowerBIIntegrationGateway

router = APIRouter(prefix="/integrations/powerbi", tags=["Microsoft Power BI Integration"])

@router.get("/status")
def get_powerbi_status(current_user: User = Depends(get_current_user)):
    gateway = PowerBIIntegrationGateway()
    return gateway.get_status()

@router.post("/export-guide")
def get_export_guide(current_user: User = Depends(get_current_user)):
    return {
        "title": "Microsoft Power BI Integration Guide",
        "steps": [
            "1. In AI Data Intelligence Platform, open any project and click 'Export Excel' or 'Export CSV'.",
            "2. Open Microsoft Power BI Desktop.",
            "3. Click 'Get Data' -> Select 'Excel Workbook' or 'Text/CSV'.",
            "4. Choose your exported file. All cleaned columns and schema types are instantly recognized without errors.",
            "5. To configure direct REST API auto-refresh, add your Azure AD Tenant ID and Client Secret to the server .env."
        ]
    }
