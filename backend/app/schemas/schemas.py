from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = "regular_user"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Project Schemas
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    dataset_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Dataset Schemas
class DatasetResponse(BaseModel):
    id: int
    project_id: int
    name: str
    original_filename: str
    file_format: str
    file_size_bytes: int
    row_count: int
    column_count: int
    quality_score: float
    quality_summary: Optional[Dict[str, Any]] = None
    schema_metadata: Optional[List[Dict[str, Any]]] = None
    is_cleaned: bool
    current_version: int
    created_at: datetime

    class Config:
        from_attributes = True

# Data Cleaning Request Schemas
class CleaningRequest(BaseModel):
    dataset_id: int
    operation_type: str # drop_duplicates, impute_missing, type_cast, outlier_trim, text_standardize
    column_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

# AI Assistant Schemas
class AIChatRequest(BaseModel):
    project_id: int
    dataset_id: Optional[int] = None
    question: str

class AIChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    sql_query: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    chart_spec: Optional[Dict[str, Any]] = None
    agent_name: str

# ML Prediction Request
class MLTrainRequest(BaseModel):
    project_id: int
    dataset_id: int
    task_type: str # regression, classification, clustering, time_series
    target_column: Optional[str] = None
    feature_columns: Optional[List[str]] = None
    algorithm: Optional[str] = None

# Report Export Request
class ReportGenerateRequest(BaseModel):
    project_id: int
    dataset_id: Optional[int] = None
    report_type: str # pptx, pdf, excel
    title: str
    include_sections: Optional[List[str]] = None
