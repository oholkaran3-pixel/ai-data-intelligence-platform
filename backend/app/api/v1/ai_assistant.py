from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Dataset, Project, AIConversation, AIMessage, ActivityHistory, User
from app.schemas.schemas import AIChatRequest, AIChatResponse
from app.core.dependencies import get_current_user
from app.ai_engine.multi_agent import MultiAgentAnalyst

router = APIRouter(prefix="/ai", tags=["AI Analyst"])

@router.post("/ask", response_model=AIChatResponse)
def ask_ai_analyst(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == req.project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    # Pick dataset: either explicit or first in project
    dataset = None
    if req.dataset_id:
        dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id, Dataset.project_id == project.id).first()
    else:
        dataset = db.query(Dataset).filter(Dataset.project_id == project.id).order_by(Dataset.created_at.desc()).first()

    if not dataset or not dataset.parquet_path:
        raise HTTPException(status_code=400, detail="No analytical dataset available in this project. Please upload data first.")

    # Get or create conversation thread
    conv = db.query(AIConversation).filter(
        AIConversation.project_id == project.id,
        AIConversation.user_id == current_user.id
    ).first()
    if not conv:
        conv = AIConversation(project_id=project.id, user_id=current_user.id, title=f"AI Data Analysis - {project.title}")
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = AIMessage(
        conversation_id=conv.id,
        role="user",
        content=req.question
    )
    db.add(user_msg)

    # Run Multi-Agent Analytical Workflow
    analyst = MultiAgentAnalyst(dataset.parquet_path, dataset.schema_metadata or {})
    result = analyst.run_query(req.question)

    # Save AI assistant message
    assistant_msg = AIMessage(
        conversation_id=conv.id,
        role="assistant",
        content=result["content"],
        sql_query=result["sql_query"],
        execution_result=result["execution_result"],
        chart_spec=result["chart_spec"],
        agent_name=result["agent_name"]
    )
    db.add(assistant_msg)

    # Record Activity History
    activity = ActivityHistory(
        user_id=current_user.id,
        project_id=project.id,
        activity_type="ai_query",
        description=f"Asked AI: '{req.question[:50]}...'",
        status="success"
    )
    db.add(activity)
    db.commit()

    return {
        "role": "assistant",
        "content": result["content"],
        "sql_query": result["sql_query"],
        "execution_result": result["execution_result"],
        "chart_spec": result["chart_spec"],
        "agent_name": result["agent_name"]
    }

@router.get("/history/{project_id}")
def get_ai_chat_history(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(AIConversation).filter(
        AIConversation.project_id == project_id,
        AIConversation.user_id == current_user.id
    ).first()
    if not conv:
        return {"messages": []}

    msgs = db.query(AIMessage).filter(AIMessage.conversation_id == conv.id).order_by(AIMessage.created_at.asc()).all()
    return {
        "conversation_id": conv.id,
        "title": conv.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sql_query": m.sql_query,
                "execution_result": m.execution_result,
                "chart_spec": m.chart_spec,
                "agent_name": m.agent_name,
                "created_at": m.created_at
            }
            for m in msgs
        ]
    }
