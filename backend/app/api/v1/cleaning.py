import os
import uuid
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Dataset, Project, CleaningOperation, ActivityHistory, User
from app.schemas.schemas import CleaningRequest, DatasetResponse
from app.core.dependencies import get_current_user
from app.data_engine.profiler import inspect_and_read_file, profile_dataset, convert_to_parquet
from app.data_engine.cleaner import DataCleaner

router = APIRouter(prefix="/cleaning", tags=["Data Cleaning"])

@router.post("/apply", response_model=DatasetResponse)
def apply_cleaning_operation(
    req: CleaningRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).join(Project).filter(
        Dataset.id == req.dataset_id,
        Project.owner_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or unauthorized")

    # Load current dataset version
    df = inspect_and_read_file(dataset.file_path, dataset.file_format)
    params = req.parameters or {}

    cleaned_df = df
    affected_rows = 0
    reason = ""

    if req.operation_type == "drop_duplicates":
        subset = params.get("subset", None)
        cleaned_df, affected_rows, reason = DataCleaner.drop_duplicates(df, subset)
    elif req.operation_type == "impute_missing":
        if not req.column_name:
            raise HTTPException(status_code=400, detail="Column name required for imputation")
        strategy = params.get("strategy", "mean")
        fill_val = params.get("fill_value", None)
        cleaned_df, affected_rows, reason = DataCleaner.impute_missing(df, req.column_name, strategy, fill_val)
    elif req.operation_type == "type_cast":
        if not req.column_name:
            raise HTTPException(status_code=400, detail="Column name required for type casting")
        target_type = params.get("target_type", "string")
        cleaned_df, affected_rows, reason = DataCleaner.type_cast(df, req.column_name, target_type)
    elif req.operation_type == "standardize_text":
        if not req.column_name:
            raise HTTPException(status_code=400, detail="Column name required for text standardization")
        case = params.get("case", "title")
        cleaned_df, affected_rows, reason = DataCleaner.standardize_text(df, req.column_name, case)
    elif req.operation_type == "outlier_trim":
        if not req.column_name:
            raise HTTPException(status_code=400, detail="Column name required for outlier trimming")
        method = params.get("method", "cap")
        cleaned_df, affected_rows, reason = DataCleaner.handle_outliers_iqr(df, req.column_name, method)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported cleaning operation: {req.operation_type}")

    # Save cleaned version non-destructively
    new_version_num = dataset.current_version + 1
    base, ext = os.path.splitext(dataset.original_filename)
    new_filename = f"{base}_v{new_version_num}{ext}"
    new_saved_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}_{new_filename}")

    # Write cleaned dataframe
    if dataset.file_format == "csv":
        cleaned_df.to_csv(new_saved_path, index=False)
    elif dataset.file_format in ["xlsx", "xls"]:
        cleaned_df.to_excel(new_saved_path, index=False)
    elif dataset.file_format == "json":
        cleaned_df.to_json(new_saved_path, orient="records")
    else:
        cleaned_df.to_parquet(new_saved_path, index=False)

    # Re-profile cleaned data
    new_quality_score, new_quality_summary, new_schema_meta = profile_dataset(cleaned_df)

    # Update parquet storage
    parquet_path = os.path.join(settings.STORAGE_DIR, "parquet", f"{uuid.uuid4().hex}.parquet")
    convert_to_parquet(cleaned_df, parquet_path)

    # Update dataset record
    dataset.file_path = new_saved_path
    dataset.parquet_path = parquet_path
    dataset.row_count = len(cleaned_df)
    dataset.column_count = len(cleaned_df.columns)
    dataset.quality_score = new_quality_score
    dataset.quality_summary = new_quality_summary
    dataset.schema_metadata = new_schema_meta
    dataset.current_version = new_version_num
    dataset.is_cleaned = True

    # Log operation lineage
    clean_op = CleaningOperation(
        dataset_id=dataset.id,
        operation_type=req.operation_type,
        column_name=req.column_name,
        parameters=params,
        affected_rows=affected_rows,
        reason=reason,
        is_applied=True
    )
    db.add(clean_op)

    # Record User Activity
    activity = ActivityHistory(
        user_id=current_user.id,
        project_id=dataset.project_id,
        activity_type="data_cleaning",
        description=f"Applied {req.operation_type}: {reason}. Quality score now {new_quality_score}%.",
        resource_id=str(dataset.id)
    )
    db.add(activity)

    db.commit()
    db.refresh(dataset)
    return dataset

@router.get("/lineage/{dataset_id}")
def get_dataset_lineage(
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

    ops = db.query(CleaningOperation).filter(CleaningOperation.dataset_id == dataset.id).order_by(CleaningOperation.created_at.asc()).all()
    
    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "current_version": dataset.current_version,
        "total_operations": len(ops),
        "history": [
            {
                "id": op.id,
                "operation": op.operation_type,
                "column": op.column_name,
                "affected_rows": op.affected_rows,
                "reason": op.reason,
                "timestamp": op.created_at
            }
            for op in ops
        ]
    }
