from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.version_control_service import VersionControlService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/version-control", tags=["Version Control"])

# Pydantic Models
class CreateVersionRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    version_type: str = Field(..., description="Version type")
    change_description: str = Field(..., description="Change description")
    version_metadata: Dict[str, Any] = Field(default={}, description="Version metadata")

class CompareVersionsRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    version_a_id: int = Field(..., description="Version A ID")
    version_b_id: int = Field(..., description="Version B ID")
    comparison_options: Dict[str, Any] = Field(default={}, description="Comparison options")

class RestoreVersionRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    target_version_id: int = Field(..., description="Target version ID")
    restore_options: Dict[str, Any] = Field(default={}, description="Restore options")

class MergeVersionsRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    source_version_ids: List[int] = Field(..., description="Source version IDs")
    merge_strategy: str = Field(..., description="Merge strategy")
    merge_options: Dict[str, Any] = Field(default={}, description="Merge options")

# Dependency
async def get_version_control_service() -> VersionControlService:
    """Get version control service instance"""
    service = VersionControlService()
    await service.initialize()
    return service

# Endpoints
@router.post("/create-version", response_model=Dict[str, Any], status_code=201)
async def create_version(
    request: CreateVersionRequest,
    service: VersionControlService = Depends(get_version_control_service)
):
    """Create new version of content"""
    try:
        result = await service.create_version(
            content_piece_id=request.content_piece_id,
            version_type=request.version_type,
            change_description=request.change_description,
            version_metadata=request.version_metadata
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create version")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Version creation failed: {str(e)}"
        )

@router.post("/compare-versions", response_model=Dict[str, Any], status_code=200)
async def compare_versions(
    request: CompareVersionsRequest,
    service: VersionControlService = Depends(get_version_control_service)
):
    """Compare two versions of content"""
    try:
        result = await service.compare_versions(
            content_piece_id=request.content_piece_id,
            version_a_id=request.version_a_id,
            version_b_id=request.version_b_id,
            comparison_options=request.comparison_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to compare versions")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Version comparison failed: {str(e)}"
        )

@router.post("/restore-version", response_model=Dict[str, Any], status_code=200)
async def restore_version(
    request: RestoreVersionRequest,
    service: VersionControlService = Depends(get_version_control_service)
):
    """Restore content to specific version"""
    try:
        result = await service.restore_version(
            content_piece_id=request.content_piece_id,
            target_version_id=request.target_version_id,
            restore_options=request.restore_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to restore version")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Version restoration failed: {str(e)}"
        )

@router.post("/merge-versions", response_model=Dict[str, Any], status_code=200)
async def merge_versions(
    request: MergeVersionsRequest,
    service: VersionControlService = Depends(get_version_control_service)
):
    """Merge multiple versions into new version"""
    try:
        result = await service.merge_versions(
            content_piece_id=request.content_piece_id,
            source_version_ids=request.source_version_ids,
            merge_strategy=request.merge_strategy,
            merge_options=request.merge_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to merge versions")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Version merging failed: {str(e)}"
        )

@router.get("/version-history/{content_piece_id}")
async def get_version_history(
    content_piece_id: int,
    service: VersionControlService = Depends(get_version_control_service)
):
    """Get version history for content piece"""
    try:
        result = await service.get_version_history(content_piece_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get version history")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Version history retrieval failed: {str(e)}"
        )

@router.get("/version-types")
async def get_version_types():
    """Get available version types for content"""
    return {
        "version_types": [
            {
                "id": "major",
                "name": "Major Version",
                "description": "Significant changes or new features",
                "characteristics": ["breaking_changes", "new_features", "major_redesign"],
                "versioning": "X.0.0",
                "use_cases": ["major_updates", "feature_releases", "redesigns"]
            },
            {
                "id": "minor",
                "name": "Minor Version",
                "description": "New features without breaking changes",
                "characteristics": ["new_features", "enhancements", "backward_compatible"],
                "versioning": "0.X.0",
                "use_cases": ["feature_additions", "enhancements", "improvements"]
            },
            {
                "id": "patch",
                "name": "Patch Version",
                "description": "Bug fixes and minor improvements",
                "characteristics": ["bug_fixes", "minor_improvements", "stability"],
                "versioning": "0.0.X",
                "use_cases": ["bug_fixes", "stability_improvements", "minor_updates"]
            },
            {
                "id": "draft",
                "name": "Draft Version",
                "description": "Work in progress version",
                "characteristics": ["unfinished", "experimental", "internal_use"],
                "versioning": "draft-X",
                "use_cases": ["work_in_progress", "experiments", "internal_review"]
            },
            {
                "id": "review",
                "name": "Review Version",
                "description": "Version ready for review",
                "characteristics": ["review_ready", "stakeholder_feedback", "approval_pending"],
                "versioning": "review-X",
                "use_cases": ["stakeholder_review", "approval_process", "feedback_collection"]
            }
        ]
    }

@router.get("/comparison-options")
async def get_comparison_options():
    """Get available options for version comparison"""
    return {
        "comparison_options": [
            {
                "id": "text_diff",
                "name": "Text Difference",
                "description": "Compare text content differences",
                "features": ["word_changes", "sentence_changes", "paragraph_changes"],
                "output_format": "diff_format",
                "best_for": ["content_changes", "text_updates", "editing_tracking"]
            },
            {
                "id": "metadata_diff",
                "name": "Metadata Difference",
                "description": "Compare metadata and properties",
                "features": ["title_changes", "tag_changes", "property_changes"],
                "output_format": "structured_diff",
                "best_for": ["property_updates", "metadata_changes", "configuration_changes"]
            },
            {
                "id": "structure_diff",
                "name": "Structure Difference",
                "description": "Compare content structure and organization",
                "features": ["section_changes", "order_changes", "hierarchy_changes"],
                "output_format": "structural_diff",
                "best_for": ["reorganization", "structure_updates", "layout_changes"]
            },
            {
                "id": "visual_diff",
                "name": "Visual Difference",
                "description": "Compare visual elements and formatting",
                "features": ["formatting_changes", "style_changes", "layout_changes"],
                "output_format": "visual_diff",
                "best_for": ["design_changes", "formatting_updates", "visual_updates"]
            }
        ]
    }

@router.get("/merge-strategies")
async def get_merge_strategies():
    """Get available strategies for merging versions"""
    return {
        "merge_strategies": [
            {
                "id": "automatic",
                "name": "Automatic Merge",
                "description": "Automatically merge compatible changes",
                "features": ["conflict_detection", "automatic_resolution", "compatibility_check"],
                "best_for": ["compatible_changes", "simple_merges", "low_conflict_scenarios"],
                "limitations": ["limited_conflict_resolution", "may_require_manual_review"]
            },
            {
                "id": "manual",
                "name": "Manual Merge",
                "description": "Manual review and resolution of conflicts",
                "features": ["conflict_highlighting", "manual_resolution", "review_interface"],
                "best_for": ["complex_changes", "high_conflict_scenarios", "critical_content"],
                "limitations": ["requires_manual_effort", "time_consuming"]
            },
            {
                "id": "priority_based",
                "name": "Priority-Based Merge",
                "description": "Merge based on version priorities",
                "features": ["priority_assignment", "conflict_resolution", "priority_override"],
                "best_for": ["hierarchical_changes", "approval_workflows", "stakeholder_priorities"],
                "limitations": ["requires_priority_setup", "may_override_important_changes"]
            },
            {
                "id": "selective",
                "name": "Selective Merge",
                "description": "Select specific changes to merge",
                "features": ["change_selection", "granular_control", "custom_merge"],
                "best_for": ["partial_merges", "selective_updates", "custom_requirements"],
                "limitations": ["requires_detailed_review", "complex_decision_making"]
            }
        ]
    }

@router.get("/restore-options")
async def get_restore_options():
    """Get available options for version restoration"""
    return {
        "restore_options": [
            {
                "id": "full_restore",
                "name": "Full Restore",
                "description": "Restore all content to target version",
                "features": ["complete_restoration", "all_properties", "full_content"],
                "use_cases": ["complete_rollback", "major_issues", "full_revert"],
                "considerations": ["loses_all_changes", "irreversible_action"]
            },
            {
                "id": "partial_restore",
                "name": "Partial Restore",
                "description": "Restore specific parts of content",
                "features": ["selective_restoration", "property_selection", "granular_control"],
                "use_cases": ["selective_rollback", "partial_issues", "targeted_revert"],
                "considerations": ["requires_careful_selection", "complex_restoration"]
            },
            {
                "id": "backup_restore",
                "name": "Backup Restore",
                "description": "Create backup before restoration",
                "features": ["automatic_backup", "restore_safety", "rollback_option"],
                "use_cases": ["safe_restoration", "experimental_restore", "risk_mitigation"],
                "considerations": ["additional_storage", "backup_management"]
            },
            {
                "id": "preview_restore",
                "name": "Preview Restore",
                "description": "Preview restoration without applying",
                "features": ["restoration_preview", "change_visualization", "safe_preview"],
                "use_cases": ["restoration_preview", "change_assessment", "safe_evaluation"],
                "considerations": ["preview_only", "requires_manual_application"]
            }
        ]
    }

@router.get("/version-metadata")
async def get_version_metadata():
    """Get available metadata fields for version tracking"""
    return {
        "version_metadata": [
            {
                "id": "change_summary",
                "name": "Change Summary",
                "description": "Brief summary of changes made",
                "type": "text",
                "required": true,
                "max_length": 500
            },
            {
                "id": "change_type",
                "name": "Change Type",
                "description": "Type of changes made",
                "type": "enum",
                "options": ["content", "formatting", "structure", "metadata", "design"],
                "required": true
            },
            {
                "id": "author",
                "name": "Author",
                "description": "Person who made the changes",
                "type": "text",
                "required": true,
                "max_length": 100
            },
            {
                "id": "reviewer",
                "name": "Reviewer",
                "description": "Person who reviewed the changes",
                "type": "text",
                "required": false,
                "max_length": 100
            },
            {
                "id": "approval_status",
                "name": "Approval Status",
                "description": "Current approval status",
                "type": "enum",
                "options": ["pending", "approved", "rejected", "needs_revision"],
                "required": false
            },
            {
                "id": "tags",
                "name": "Tags",
                "description": "Tags for categorization",
                "type": "array",
                "required": false,
                "max_items": 10
            }
        ]
    }
