import os
import shutil
import uuid
import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Dataset, Project, ActivityHistory, User
from app.schemas.schemas import DatasetResponse
from app.core.dependencies import get_current_user
from app.data_engine.profiler import inspect_and_read_file, profile_dataset, convert_to_parquet

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    project_id: int = Form(...),
    name: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    # Validate file extension
    filename = file.filename or "uploaded_data"
    ext = os.path.splitext(filename)[1].lower().replace(".", "")
    allowed_exts = ["csv", "xlsx", "xls", "json", "parquet", "txt"]
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Allowed: {', '.join(allowed_exts)}")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_DIR, "parquet"), exist_ok=True)

    # Save incoming file
    unique_file_id = f"{uuid.uuid4().hex}_{filename}"
    saved_file_path = os.path.join(settings.UPLOAD_DIR, unique_file_id)
    
    with open(saved_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(saved_file_path)
    
    # Read file and profile
    df = inspect_and_read_file(saved_file_path, ext)
    quality_score, quality_summary, schema_meta = profile_dataset(df)
    
    # Save optimized Parquet analytical file
    parquet_filename = f"{uuid.uuid4().hex}.parquet"
    parquet_path = os.path.join(settings.STORAGE_DIR, "parquet", parquet_filename)
    convert_to_parquet(df, parquet_path)
    
    dataset_name = name or os.path.splitext(filename)[0].replace("_", " ").title()

    new_dataset = Dataset(
        project_id=project.id,
        name=dataset_name,
        original_filename=filename,
        file_format=ext,
        file_size_bytes=file_size,
        file_path=saved_file_path,
        parquet_path=parquet_path,
        row_count=len(df),
        column_count=len(df.columns),
        quality_score=quality_score,
        quality_summary=quality_summary,
        schema_metadata=schema_meta,
        is_cleaned=False,
        current_version=1
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)

    # Record Activity History
    activity = ActivityHistory(
        user_id=current_user.id,
        project_id=project.id,
        activity_type="data_upload",
        description=f"Uploaded dataset '{new_dataset.name}' ({len(df)} rows, Quality Score: {quality_score}%)",
        resource_id=str(new_dataset.id)
    )
    db.add(activity)
    db.commit()

    return new_dataset

@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    project_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Dataset).join(Project).filter(Project.owner_id == current_user.id)
    if project_id:
        query = query.filter(Dataset.project_id == project_id)
    return query.order_by(Dataset.created_at.desc()).all()

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).join(Project).filter(
        Dataset.id == dataset_id,
        Project.owner_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or unauthorized")
    return dataset

@router.get("/{dataset_id}/preview")
def get_dataset_preview(
    dataset_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).join(Project).filter(
        Dataset.id == dataset_id,
        Project.owner_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or unauthorized")
        
    df = inspect_and_read_file(dataset.file_path, dataset.file_format)
    total_records = len(df)
    paged_df = df.iloc[offset : offset + limit]
    
    # Clean NaN/Infinity for valid JSON serialization
    paged_df = paged_df.replace({np.nan: None, np.inf: None, -np.inf: None})
    
    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "total_rows": total_records,
        "limit": limit,
        "offset": offset,
        "columns": list(df.columns),
        "data": paged_df.to_dict(orient="records")
    }

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).join(Project).filter(
        Dataset.id == dataset_id,
        Project.owner_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Remove files if they exist
    if os.path.exists(dataset.file_path):
        try:
            os.remove(dataset.file_path)
        except Exception:
            pass
    if dataset.parquet_path and os.path.exists(dataset.parquet_path):
        try:
            os.remove(dataset.parquet_path)
        except Exception:
            pass

    db.delete(dataset)
    db.commit()
    return None
