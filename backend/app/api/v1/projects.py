from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Project, Dataset, Report, AnalysisResult, ActivityHistory, User
from app.schemas.schemas import ProjectCreate, ProjectResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = Project(
        title=project_in.title,
        description=project_in.description,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    activity = ActivityHistory(
        user_id=current_user.id,
        project_id=project.id,
        activity_type="project_create",
        description=f"Created project '{project.title}'",
        resource_id=str(project.id)
    )
    db.add(activity)
    db.commit()
    
    return project

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce strict user data isolation
    projects = db.query(Project).filter(
        Project.owner_id == current_user.id,
        Project.is_archived == False
    ).order_by(Project.created_at.desc()).all()
    
    # Enrich with dataset count
    results = []
    for p in projects:
        count = db.query(Dataset).filter(Dataset.project_id == p.id).count()
        p_resp = ProjectResponse.from_orm(p)
        p_resp.dataset_count = count
        results.append(p_resp)
        
    return results

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
        
    count = db.query(Dataset).filter(Dataset.project_id == project.id).count()
    resp = ProjectResponse.from_orm(project)
    resp.dataset_count = count
    return resp

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    db.delete(project)
    
    activity = ActivityHistory(
        user_id=current_user.id,
        activity_type="project_delete",
        description=f"Deleted project '{project.title}'"
    )
    db.add(activity)
    db.commit()
    return None
