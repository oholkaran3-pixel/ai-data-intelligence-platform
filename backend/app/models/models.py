import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="regular_user", nullable=False) # regular_user, admin, org_owner, org_member
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    activities = relationship("ActivityHistory", back_populates="user", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="members")

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    members = relationship("User", back_populates="organization")
    projects = relationship("Project", back_populates="organization")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    organization = relationship("Organization", back_populates="projects")
    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")
    analyses = relationship("AnalysisResult", back_populates="project", cascade="all, delete-orphan")
    dashboards = relationship("Dashboard", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")
    ai_conversations = relationship("AIConversation", back_populates="project", cascade="all, delete-orphan")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_format = Column(String(50), nullable=False) # csv, xlsx, json, parquet, pdf, etc.
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    parquet_path = Column(String(500), nullable=True) # Optimized analytical parquet storage
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    quality_score = Column(Float, default=100.0) # Calculated 0.0 - 100.0
    quality_summary = Column(JSON, nullable=True) # Full profile breakdown & issues
    schema_metadata = Column(JSON, nullable=True) # Column names, detected types, null counts
    is_cleaned = Column(Boolean, default=False)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="datasets")
    cleaning_ops = relationship("CleaningOperation", back_populates="dataset", cascade="all, delete-orphan")
    visualizations = relationship("Visualization", back_populates="dataset", cascade="all, delete-orphan")

class CleaningOperation(Base):
    __tablename__ = "cleaning_operations"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    operation_type = Column(String(100), nullable=False) # drop_duplicates, impute_missing, type_cast, outlier_trim, text_standardize
    column_name = Column(String(255), nullable=True)
    parameters = Column(JSON, nullable=True)
    affected_rows = Column(Integer, default=0)
    reason = Column(Text, nullable=True)
    is_applied = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dataset = relationship("Dataset", back_populates="cleaning_ops")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    analysis_type = Column(String(100), nullable=False) # eda, correlation, time_series, ml_regression, ml_classification, ml_clustering
    title = Column(String(255), nullable=False)
    summary = Column(JSON, nullable=False) # Statistical summary, metrics, evaluation
    charts_spec = Column(JSON, nullable=True) # Pre-computed Plotly specs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="analyses")

class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    title = Column(String(255), nullable=False)
    chart_type = Column(String(50), nullable=False) # bar, line, scatter, pie, histogram, heatmap, box, area
    config = Column(JSON, nullable=False) # x, y, color, aggregation, filters
    plotly_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dataset = relationship("Dataset", back_populates="visualizations")

class Dashboard(Base):
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    layout = Column(JSON, nullable=True) # Grid layout & widget assignments
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="dashboards")
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")

class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"), nullable=False)
    widget_type = Column(String(50), nullable=False) # kpi_card, chart, data_table, text_note
    title = Column(String(255), nullable=False)
    content = Column(JSON, nullable=False) # Widget config, query, or kpi formula
    position = Column(JSON, nullable=True) # {x, y, w, h}

    dashboard = relationship("Dashboard", back_populates="widgets")

class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="Data Analysis Assistant")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="ai_conversations")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")

class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False)
    role = Column(String(50), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=True)
    execution_result = Column(JSON, nullable=True)
    chart_spec = Column(JSON, nullable=True)
    agent_name = Column(String(100), nullable=True) # DataUnderstandingAgent, EDAAgent, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("AIConversation", back_populates="messages")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False) # pptx, pdf, excel
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    config = Column(JSON, nullable=True) # Included sections, charts, notes
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="reports")

class ActivityHistory(Base):
    __tablename__ = "activity_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    activity_type = Column(String(100), nullable=False) # login, upload, clean, eda, ml_train, report_export, pbi_sync
    description = Column(Text, nullable=False)
    status = Column(String(50), default="success") # success, pending, failed
    resource_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="activities")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    target_resource = Column(String(100), nullable=True)
    ip_address = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
