import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.utils.nlp_utils import NLPProcessor
from backend.core.cache.redis_manager import RedisManager
from ..models import CollaborationProject, JackieTeamMember, Comment, Review, Version, JackieTask

class CampaignCollaborationService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_collaboration_project(self, project_name: str, project_type: str,
                                   team_members: List[Dict[str, Any]], project_settings: Dict[str, Any]) -> Dict[str, Any]:
        project_id = str(uuid.uuid4())
        
        project = CollaborationProject(
            id=project_id, project_name=project_name, project_type=project_type,
            team_members=json.dumps(team_members), project_settings=json.dumps(project_settings),
            status="active", created_at=datetime.utcnow()
        )
        self.db.add(project)
        self.db.commit()
        
        return {
            "project_id": project_id, "project_name": project_name,
            "project_type": project_type, "status": "active",
            "created_at": project.created_at.isoformat()
        }
    
    def add_team_member(self, project_id: str, member_data: Dict[str, Any]) -> Dict[str, Any]:
        project = self.db.query(CollaborationProject).filter(CollaborationProject.id == project_id).first()
        if not project:
            raise Exception("Collaboration project not found")
        
        member_id = str(uuid.uuid4())
        member = JackieTeamMember(
            id=member_id, project_id=project_id, user_id=member_data.get("user_id"),
            role=member_data.get("role", "member"), permissions=json.dumps(member_data.get("permissions", [])),
            joined_at=datetime.utcnow()
        )
        self.db.add(member)
        self.db.commit()
        
        return {
            "member_id": member_id, "project_id": project_id,
            "user_id": member_data.get("user_id"), "role": member_data.get("role", "member")
        }
    
    def remove_team_member(self, project_id: str, user_id: str) -> Dict[str, Any]:
        member = self.db.query(JackieTeamMember).filter(
            JackieTeamMember.project_id == project_id,
            JackieTeamMember.user_id == user_id
        ).first()
        
        if not member:
            raise Exception("Team member not found")
        
        self.db.delete(member)
        self.db.commit()
        
        return {
            "project_id": project_id, "user_id": user_id,
            "status": "removed", "removed_at": datetime.utcnow().isoformat()
        }
    
    def add_comment(self, project_id: str, user_id: str, content: str,
                   comment_type: str = "general", parent_comment_id: Optional[str] = None) -> Dict[str, Any]:
        comment_id = str(uuid.uuid4())
        
        comment = Comment(
            id=comment_id, project_id=project_id, user_id=user_id, content=content,
            comment_type=comment_type, parent_comment_id=parent_comment_id,
            created_at=datetime.utcnow()
        )
        self.db.add(comment)
        self.db.commit()
        
        return {
            "comment_id": comment_id, "project_id": project_id,
            "user_id": user_id, "content": content, "comment_type": comment_type,
            "created_at": comment.created_at.isoformat()
        }
    
    def update_comment(self, comment_id: str, new_content: str) -> Dict[str, Any]:
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise Exception("Comment not found")
        
        comment.content = new_content
        comment.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {
            "comment_id": comment_id, "new_content": new_content,
            "updated_at": comment.updated_at.isoformat()
        }
    
    def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise Exception("Comment not found")
        
        self.db.delete(comment)
        self.db.commit()
        
        return {
            "comment_id": comment_id, "status": "deleted",
            "deleted_at": datetime.utcnow().isoformat()
        }
    
    def create_review(self, project_id: str, reviewer_id: str, review_data: Dict[str, Any]) -> Dict[str, Any]:
        review_id = str(uuid.uuid4())
        
        review = Review(
            id=review_id, project_id=project_id, reviewer_id=reviewer_id,
            review_type=review_data.get("review_type", "general"),
            review_content=json.dumps(review_data.get("review_content", {})),
            status=review_data.get("status", "pending"), created_at=datetime.utcnow()
        )
        self.db.add(review)
        self.db.commit()
        
        return {
            "review_id": review_id, "project_id": project_id,
            "reviewer_id": reviewer_id, "status": review_data.get("status", "pending"),
            "created_at": review.created_at.isoformat()
        }
    
    def manage_review(self, review_id: str, action: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise Exception("Review not found")
        
        if action == "approve":
            review.status = "approved"
            review.approved_at = datetime.utcnow()
        elif action == "reject":
            review.status = "rejected"
            review.rejected_at = datetime.utcnow()
            review.rejection_reason = action_data.get("reason", "")
        elif action == "request_changes":
            review.status = "changes_requested"
            review.changes_requested = json.dumps(action_data.get("changes", []))
        
        self.db.commit()
        
        return {
            "review_id": review_id, "action": action,
            "new_status": review.status, "updated_at": datetime.utcnow().isoformat()
        }
    
    def create_version(self, project_id: str, version_data: Dict[str, Any]) -> Dict[str, Any]:
        version_id = str(uuid.uuid4())
        
        version = Version(
            id=version_id, project_id=project_id, version_number=version_data.get("version_number"),
            version_name=version_data.get("version_name", ""), changes=json.dumps(version_data.get("changes", [])),
            created_by=version_data.get("created_by"), created_at=datetime.utcnow()
        )
        self.db.add(version)
        self.db.commit()
        
        return {
            "version_id": version_id, "project_id": project_id,
            "version_number": version_data.get("version_number"),
            "version_name": version_data.get("version_name", ""),
            "created_at": version.created_at.isoformat()
        }
    
    def revert_version(self, project_id: str, target_version_id: str) -> Dict[str, Any]:
        target_version = self.db.query(Version).filter(Version.id == target_version_id).first()
        if not target_version:
            raise Exception("Target version not found")
        
        revert_id = str(uuid.uuid4())
        revert_version = Version(
            id=revert_id, project_id=project_id, version_number=f"revert_{target_version.version_number}",
            version_name=f"Revert to {target_version.version_name}", changes=json.dumps(["Reverted to previous version"]),
            created_by="system", created_at=datetime.utcnow()
        )
        self.db.add(revert_version)
        self.db.commit()
        
        return {
            "revert_id": revert_id, "project_id": project_id,
            "target_version_id": target_version_id,
            "reverted_at": revert_version.created_at.isoformat()
        }
    
    def create_task(self, project_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        
        task = JackieTask(
            id=task_id, project_id=project_id, task_name=task_data.get("task_name"),
            task_description=task_data.get("task_description", ""),
            assigned_to=task_data.get("assigned_to"), priority=task_data.get("priority", "medium"),
            due_date=task_data.get("due_date"), status=task_data.get("status", "pending"),
            created_at=datetime.utcnow()
        )
        self.db.add(task)
        self.db.commit()
        
        return {
            "task_id": task_id, "project_id": project_id,
            "task_name": task_data.get("task_name"), "assigned_to": task_data.get("assigned_to"),
            "status": task_data.get("status", "pending"), "created_at": task.created_at.isoformat()
        }
    
    def update_task_status(self, task_id: str, new_status: str, update_notes: Optional[str] = None) -> Dict[str, Any]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise Exception("Task not found")
        
        task.status = new_status
        task.updated_at = datetime.utcnow()
        if update_notes:
            task.notes = update_notes
        
        self.db.commit()
        
        return {
            "task_id": task_id, "new_status": new_status,
            "updated_at": task.updated_at.isoformat()
        }
    
    def send_notification(self, project_id: str, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Project ID: {project_id}
        Notification Data: {notification_data}
        
        Generate appropriate notification content and determine recipients.
        """
        
        notification_result = self.nlp_processor.generate_notification(prompt)
        
        return {
            "project_id": project_id, "notification_type": notification_data.get("type"),
            "recipients": notification_result.get("recipients", []),
            "notification_content": notification_result.get("content", ""),
            "sent_at": datetime.utcnow().isoformat()
        }
    
    def manage_approvals(self, project_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Project ID: {project_id}
        Approval Data: {approval_data}
        
        Process approval workflow and determine next steps.
        """
        
        approval_result = self.nlp_processor.process_approval_workflow(prompt)
        
        return {
            "project_id": project_id, "approval_type": approval_data.get("type"),
            "approval_status": approval_result.get("status", "pending"),
            "approvers": approval_result.get("approvers", []),
            "next_steps": approval_result.get("next_steps", [])
        }
    
    def get_collaboration_analytics(self, project_id: str, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        team_members = self.db.query(JackieTeamMember).filter(JackieTeamMember.project_id == project_id).count()
        
        comments = self.db.query(Comment).filter(
            Comment.project_id == project_id,
            Comment.created_at >= cutoff_date
        ).count()
        
        reviews = self.db.query(Review).filter(
            Review.project_id == project_id,
            Review.created_at >= cutoff_date
        ).count()
        
        tasks = self.db.query(Task).filter(
            Task.project_id == project_id,
            Task.created_at >= cutoff_date
        ).count()
        
        completed_tasks = self.db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "completed",
            Task.created_at >= cutoff_date
        ).count()
        
        return {
            "project_id": project_id, "timeframe": timeframe,
            "team_members": team_members, "comments": comments,
            "reviews": reviews, "total_tasks": tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": (completed_tasks / tasks * 100) if tasks > 0 else 0
        }
    
    def get_project_timeline(self, project_id: str) -> Dict[str, Any]:
        project = self.db.query(CollaborationProject).filter(CollaborationProject.id == project_id).first()
        if not project:
            raise Exception("Collaboration project not found")
        
        comments = self.db.query(Comment).filter(Comment.project_id == project_id).order_by(Comment.created_at.desc()).limit(10).all()
        reviews = self.db.query(Review).filter(Review.project_id == project_id).order_by(Review.created_at.desc()).limit(5).all()
        versions = self.db.query(Version).filter(Version.project_id == project_id).order_by(Version.created_at.desc()).limit(5).all()
        tasks = self.db.query(Task).filter(Task.project_id == project_id).order_by(Task.created_at.desc()).limit(10).all()
        
        timeline = []
        
        for comment in comments:
            timeline.append({
                "type": "comment", "id": comment.id, "content": comment.content,
                "user_id": comment.user_id, "created_at": comment.created_at.isoformat()
            })
        
        for review in reviews:
            timeline.append({
                "type": "review", "id": review.id, "status": review.status,
                "reviewer_id": review.reviewer_id, "created_at": review.created_at.isoformat()
            })
        
        for version in versions:
            timeline.append({
                "type": "version", "id": version.id, "version_number": version.version_number,
                "version_name": version.version_name, "created_at": version.created_at.isoformat()
            })
        
        for task in tasks:
            timeline.append({
                "type": "task", "id": task.id, "task_name": task.task_name,
                "status": task.status, "created_at": task.created_at.isoformat()
            })
        
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "project_id": project_id, "project_name": project.project_name,
            "timeline": timeline[:20]  # Return last 20 events
        }
    
    def export_project_data(self, project_id: str, export_format: str = "json") -> Dict[str, Any]:
        project = self.db.query(CollaborationProject).filter(CollaborationProject.id == project_id).first()
        if not project:
            raise Exception("Collaboration project not found")
        
        team_members = self.db.query(JackieTeamMember).filter(JackieTeamMember.project_id == project_id).all()
        comments = self.db.query(Comment).filter(Comment.project_id == project_id).all()
        reviews = self.db.query(Review).filter(Review.project_id == project_id).all()
        versions = self.db.query(Version).filter(Version.project_id == project_id).all()
        tasks = self.db.query(JackieTask).filter(JackieTask.project_id == project_id).all()
        
        export_data = {
            "project": {
                "id": project.id, "name": project.project_name,
                "type": project.project_type, "status": project.status,
                "created_at": project.created_at.isoformat()
            },
            "team_members": [{"id": m.id, "user_id": m.user_id, "role": m.role} for m in team_members],
            "comments": [{"id": c.id, "content": c.content, "user_id": c.user_id} for c in comments],
            "reviews": [{"id": r.id, "status": r.status, "reviewer_id": r.reviewer_id} for r in reviews],
            "versions": [{"id": v.id, "version_number": v.version_number, "name": v.version_name} for v in versions],
            "tasks": [{"id": t.id, "name": t.task_name, "status": t.status, "assigned_to": t.assigned_to} for t in tasks]
        }
        
        return {
            "project_id": project_id, "export_format": export_format,
            "export_data": export_data, "exported_at": datetime.utcnow().isoformat()
        }
