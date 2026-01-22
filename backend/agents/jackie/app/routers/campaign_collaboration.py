from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.campaign_collaboration_service import CampaignCollaborationService

router = APIRouter(prefix="/campaign-collaboration", tags=["Campaign Collaboration Tools"])
from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    campaign_type: str
    team_members: List[str]
    settings: Optional[Dict[str, Any]] = None


class AddCommentRequest(BaseModel):
    content: str
    comment_type: str = "general"
    parent_comment_id: Optional[str] = None
    mentions: Optional[List[str]] = None


class ReviewRequest(BaseModel):
    reviewer_id: str
    review_type: str
    feedback: Dict[str, Any]
    status: str = "pending"


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    campaign_type: str
    team_members: List[str]
    status: str
    created_at: datetime

@router.post("/projects", response_model=ProjectResponse)
async def create_collaboration_project(
    request: CreateProjectRequest,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.create_collaboration_project(
            request.name,
            request.description,
            request.campaign_type,
            request.team_members,
            request.settings
        )
        return ProjectResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            campaign_type=result["campaign_type"],
            team_members=result["team_members"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_collaboration_project(project_id: str, db: Session = Depends(get_db)):
    service = CampaignCollaborationService(db)
    try:
        result = service.get_collaboration_project(project_id)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            campaign_type=result["campaign_type"],
            team_members=result["team_members"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects", response_model=List[ProjectResponse])
async def list_collaboration_projects(
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        results = service.list_collaboration_projects(status, campaign_type, limit, offset)
        return [
            ProjectResponse(
                id=result["id"],
                name=result["name"],
                description=result["description"],
                campaign_type=result["campaign_type"],
                team_members=result["team_members"],
                status=result["status"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/projects/{project_id}")
async def update_collaboration_project(
    project_id: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.update_collaboration_project(project_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}")
async def delete_collaboration_project(project_id: str, db: Session = Depends(get_db)):
    service = CampaignCollaborationService(db)
    try:
        result = service.delete_collaboration_project(project_id)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/members/add")
async def add_project_member(
    project_id: str,
    member_id: str,
    role: str = "member",
    permissions: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.add_project_member(project_id, member_id, role, permissions)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Member added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}/members/{member_id}")
async def remove_project_member(
    project_id: str,
    member_id: str,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.remove_project_member(project_id, member_id)
        if not result:
            raise HTTPException(status_code=404, detail="Project or member not found")
        return {"message": "Member removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/members")
async def get_project_members(project_id: str, db: Session = Depends(get_db)):
    service = CampaignCollaborationService(db)
    try:
        members = service.get_project_members(project_id)
        if not members:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"members": members}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/comments")
async def add_project_comment(
    project_id: str,
    request: AddCommentRequest,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.add_project_comment(
            project_id,
            request.content,
            request.comment_type,
            request.parent_comment_id,
            request.mentions
        )
        return {
            "message": "JackieComment added successfully",
            "comment_id": result["comment_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/comments")
async def get_project_comments(
    project_id: str,
    comment_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        comments = service.get_project_comments(project_id, comment_type, limit, offset)
        return {"comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/comments/{comment_id}")
async def update_project_comment(
    comment_id: str,
    content: str,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.update_project_comment(comment_id, content)
        if not result:
            raise HTTPException(status_code=404, detail="JackieComment not found")
        return {"message": "JackieComment updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/comments/{comment_id}")
async def delete_project_comment(comment_id: str, db: Session = Depends(get_db)):
    service = CampaignCollaborationService(db)
    try:
        result = service.delete_project_comment(comment_id)
        if not result:
            raise HTTPException(status_code=404, detail="JackieComment not found")
        return {"message": "JackieComment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/reviews")
async def create_project_review(
    project_id: str,
    request: ReviewRequest,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.create_project_review(
            project_id,
            request.reviewer_id,
            request.review_type,
            request.feedback,
            request.status
        )
        return {
            "message": "JackieReview created successfully",
            "review_id": result["review_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/reviews")
async def get_project_reviews(
    project_id: str,
    review_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        reviews = service.get_project_reviews(project_id, review_type, status, limit, offset)
        return {"reviews": reviews}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/reviews/{review_id}/status")
async def update_review_status(
    review_id: str,
    status: str,
    feedback: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.update_review_status(review_id, status, feedback)
        if not result:
            raise HTTPException(status_code=404, detail="JackieReview not found")
        return {"message": "JackieReview status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/versions/create")
async def create_project_version(
    project_id: str,
    version_name: str,
    version_description: str,
    changes: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.create_project_version(project_id, version_name, version_description, changes)
        return {
            "message": "JackieVersion created successfully",
            "version_id": result["version_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/versions")
async def get_project_versions(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        versions = service.get_project_versions(project_id, limit, offset)
        return {"versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/versions/{version_id}")
async def get_version_details(version_id: str, db: Session = Depends(get_db)):
    service = CampaignCollaborationService(db)
    try:
        version = service.get_version_details(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="JackieVersion not found")
        return version
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/versions/{version_id}/revert")
async def revert_to_version(version_id: str, db: Session = Depends(get_db)):
    service = CampaignCollaborationService(db)
    try:
        result = service.revert_to_version(version_id)
        if not result:
            raise HTTPException(status_code=404, detail="JackieVersion not found")
        return {"message": "Project reverted to version successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/tasks/create")
async def create_project_task(
    project_id: str,
    task_name: str,
    task_description: str,
    assignee_id: str,
    due_date: Optional[str] = None,
    priority: str = "medium",
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.create_project_task(project_id, task_name, task_description, assignee_id, due_date, priority)
        return {
            "message": "Task created successfully",
            "task_id": result["task_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/tasks")
async def get_project_tasks(
    project_id: str,
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        tasks = service.get_project_tasks(project_id, status, assignee_id, limit, offset)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    completion_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.update_task_status(task_id, status, completion_notes)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/notifications/send")
async def send_project_notification(
    project_id: str,
    notification_type: str,
    message: str,
    recipients: List[str],
    priority: str = "normal",
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.send_project_notification(project_id, notification_type, message, recipients, priority)
        return {
            "message": "Notification sent successfully",
            "notification_id": result["notification_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications")
async def get_user_notifications(
    user_id: str,
    notification_type: Optional[str] = None,
    read_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        notifications = service.get_user_notifications(user_id, notification_type, read_status, limit, offset)
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    service = CampaignCollaborationService(db)
    try:
        result = service.mark_notification_read(notification_id)
        if not result:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/approvals/request")
async def request_project_approval(
    project_id: str,
    approval_type: str,
    approver_id: str,
    request_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.request_project_approval(project_id, approval_type, approver_id, request_notes)
        return {
            "message": "Approval requested successfully",
            "approval_id": result["approval_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/approvals")
async def get_project_approvals(
    project_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        approvals = service.get_project_approvals(project_id, status, limit, offset)
        return {"approvals": approvals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/approvals/{approval_id}/respond")
async def respond_to_approval(
    approval_id: str,
    response: str,
    response_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        result = service.respond_to_approval(approval_id, response, response_notes)
        if not result:
            raise HTTPException(status_code=404, detail="Approval not found")
        return {"message": "Approval response submitted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_collaboration_analytics_overview(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        overview = service.get_collaboration_analytics_overview(timeframe)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{project_id}/performance")
async def get_project_collaboration_performance(
    project_id: str,
    metrics: List[str],
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = CampaignCollaborationService(db)
    try:
        performance = service.get_project_collaboration_performance(project_id, metrics, timeframe)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
