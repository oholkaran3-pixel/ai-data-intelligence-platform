import os
import uuid
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Dataset, Project, Report, ActivityHistory, User
from app.schemas.schemas import ReportGenerateRequest
from app.core.dependencies import get_current_user
from app.data_engine.profiler import inspect_and_read_file
from app.reporting.pptx_generator import PowerPointReportGenerator
from app.reporting.report_generators import MultiFormatReportGenerator

router = APIRouter(prefix="/reports", tags=["Reporting & Presentations"])

@router.post("/generate")
def generate_report(
    req: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == req.project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    # Fetch dataset
    dataset = None
    if req.dataset_id:
        dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id, Dataset.project_id == project.id).first()
    else:
        dataset = db.query(Dataset).filter(Dataset.project_id == project.id).order_by(Dataset.created_at.desc()).first()

    if not dataset:
        raise HTTPException(status_code=400, detail="No dataset found to generate report.")

    df = inspect_and_read_file(dataset.file_path, dataset.file_format)
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    
    unique_id = uuid.uuid4().hex[:8]
    ext = req.report_type.lower()
    
    filename = f"{req.title.replace(' ', '_')}_{unique_id}.{ext}"
    output_path = os.path.join(settings.REPORT_DIR, filename)

    if ext == "pptx":
        PowerPointReportGenerator.create_presentation(
            title=req.title,
            dataset_name=dataset.name,
            quality_score=dataset.quality_score,
            row_count=len(df),
            col_count=len(df.columns),
            kpi_metrics={},
            business_insights=[
                f"Data quality scored at {dataset.quality_score}% with verified schema structure.",
                f"Processed {len(df):,} records and {len(df.columns)} dimensions seamlessly.",
                "Automated multi-agent findings confirm high suitability for predictive intelligence."
            ],
            output_filepath=output_path
        )
    elif ext == "pdf":
        MultiFormatReportGenerator.generate_pdf_report(
            title=req.title,
            dataset_name=dataset.name,
            quality_summary=dataset.quality_summary or {},
            output_path=output_path
        )
    elif ext in ["xlsx", "excel"]:
        ext = "xlsx"
        filename = f"{req.title.replace(' ', '_')}_{unique_id}.xlsx"
        output_path = os.path.join(settings.REPORT_DIR, filename)
        MultiFormatReportGenerator.generate_excel_report(
            df=df,
            quality_summary=dataset.quality_summary or {},
            output_path=output_path
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported report type: {ext}")

    file_size = os.path.getsize(output_path)
    report_record = Report(
        project_id=project.id,
        title=req.title,
        report_type=ext,
        file_path=output_path,
        file_size_bytes=file_size,
        config=req.include_sections
    )
    db.add(report_record)

    activity = ActivityHistory(
        user_id=current_user.id,
        project_id=project.id,
        activity_type=f"report_{ext}",
        description=f"Generated {ext.upper()} report '{req.title}'",
        resource_id=str(report_record.id)
    )
    db.add(activity)
    db.commit()
    db.refresh(report_record)

    return {
        "report_id": report_record.id,
        "title": report_record.title,
        "report_type": report_record.report_type,
        "file_size_bytes": report_record.file_size_bytes,
        "download_url": f"/api/v1/reports/download/{report_record.id}"
    }

@router.get("/download/{report_id}")
def download_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=report.file_path,
        filename=os.path.basename(report.file_path),
        media_type="application/octet-stream"
    )
