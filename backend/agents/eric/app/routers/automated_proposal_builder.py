from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..services.automated_proposal_builder_service import (
    AutomatedProposalBuilderService, GeneratedProposal, ProposalTemplate
)
from ..database import get_db
from core.authentication.auth import get_current_user
from ..models import EricSalesRep

router = APIRouter(prefix="/automated-proposal-builder", tags=["Automated Proposal Builder"])

# Initialize service
proposal_service = AutomatedProposalBuilderService()


class ProposalGenerationRequest(BaseModel):
    template_id: str = "standard"
    branding_options: Optional[Dict[str, Any]] = None


class ProposalCustomizationRequest(BaseModel):
    customizations: Dict[str, Any]


@router.post("/generate/{deal_id}")
async def generate_proposal(
    deal_id: int,
    generation_request: ProposalGenerationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> GeneratedProposal:
    """Generate a comprehensive sales proposal for a deal"""
    try:
        proposal = await proposal_service.generate_proposal(
            db=db,
            deal_id=deal_id,
            template_id=generation_request.template_id,
            branding_options=generation_request.branding_options
        )
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate proposal: {str(e)}")


@router.get("/templates")
async def get_proposal_templates(
    category: Optional[str] = Query(None, description="Filter by template category"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[ProposalTemplate]:
    """Get available proposal templates"""
    try:
        templates = await proposal_service.get_proposal_templates(
            db=db,
            category=category
        )
        return templates
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.post("/customize/{proposal_id}")
async def customize_proposal(
    proposal_id: str,
    customization_request: ProposalCustomizationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> GeneratedProposal:
    """Customize an existing proposal"""
    try:
        proposal = await proposal_service.customize_proposal(
            db=db,
            proposal_id=proposal_id,
            customizations=customization_request.customizations
        )
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to customize proposal: {str(e)}")


@router.get("/analytics/{sales_rep_id}")
async def get_proposal_analytics(
    sales_rep_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics for proposal generation and performance"""
    try:
        analytics = await proposal_service.get_proposal_analytics(
            db=db,
            sales_rep_id=sales_rep_id,
            date_range=date_range
        )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/templates/categories")
async def get_template_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available template categories"""
    try:
        templates = await proposal_service.get_proposal_templates(db=db)
        
        # Group templates by category
        categories = {}
        for template in templates:
            category = template.category
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description
            })
        
        return {
            "categories": categories,
            "total_templates": len(templates),
            "total_categories": len(categories)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/templates/{template_id}/preview")
async def get_template_preview(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get preview of a specific template"""
    try:
        templates = await proposal_service.get_proposal_templates(db=db)
        template = next((t for t in templates if t.template_id == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "template": template.dict(),
            "preview_data": {
                "sample_content": {
                    "title": "Sample Proposal",
                    "customer_name": "John Doe",
                    "company_name": "Sample Corp",
                    "deal_value": 50000,
                    "sections": template.sections
                },
                "branding_preview": template.branding_options
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template preview: {str(e)}")


@router.post("/templates/{template_id}/clone")
async def clone_template(
    template_id: str,
    new_name: str = Query(..., description="Name for the cloned template"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clone an existing template with customizations"""
    try:
        templates = await proposal_service.get_proposal_templates(db=db)
        original_template = next((t for t in templates if t.template_id == template_id), None)
        
        if not original_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create cloned template
        cloned_template_id = f"custom_{template_id}_{int(datetime.now().timestamp())}"
        cloned_template = ProposalTemplate(
            template_id=cloned_template_id,
            name=new_name,
            description=f"Customized version of {original_template.name}",
            category=original_template.category,
            sections=original_template.sections,
            branding_options=original_template.branding_options,
            is_active=True
        )
        
        return {
            "message": "Template cloned successfully",
            "original_template": original_template.dict(),
            "cloned_template": cloned_template.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clone template: {str(e)}")


@router.get("/performance/team/{team_id}")
async def get_team_proposal_performance(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get team-wide proposal performance metrics"""
    try:
        # Get all sales reps in the team
        sales_reps = db.query(EricSalesRep).filter(EricSalesRep.team_id == team_id).all()
        
        if not sales_reps:
            raise HTTPException(status_code=404, detail="Team not found")
        
        team_analytics = []
        total_proposals = 0
        total_value = 0
        total_conversions = 0
        
        for rep in sales_reps:
            try:
                analytics = await proposal_service.get_proposal_analytics(
                    db=db,
                    sales_rep_id=rep.id,
                    date_range=date_range
                )
                team_analytics.append({
                    "sales_rep_id": rep.id,
                    "sales_rep_name": f"{rep.first_name} {rep.last_name}",
                    "analytics": analytics
                })
                
                total_proposals += analytics["metrics"]["total_proposals"]
                total_value += analytics["metrics"]["total_value"]
                total_conversions += analytics["metrics"]["converted_proposals"]
                
            except Exception as e:
                # Continue with other reps if one fails
                continue
        
        # Calculate team averages
        avg_proposal_value = total_value / total_proposals if total_proposals > 0 else 0
        team_conversion_rate = (total_conversions / total_proposals * 100) if total_proposals > 0 else 0
        
        return {
            "team_id": team_id,
            "date_range": date_range,
            "team_summary": {
                "total_proposals": total_proposals,
                "total_value": total_value,
                "avg_proposal_value": avg_proposal_value,
                "total_conversions": total_conversions,
                "team_conversion_rate": team_conversion_rate,
                "active_sales_reps": len(sales_reps)
            },
            "individual_performance": team_analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team performance: {str(e)}")


@router.get("/export/{proposal_id}")
async def export_proposal(
    proposal_id: str,
    format: str = Query("pdf", description="Export format: pdf, docx, html"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export proposal in different formats"""
    try:
        # Get proposal
        proposal = await proposal_service._get_proposal_by_id(db, proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Generate export URL based on format
        if format == "pdf":
            export_url = proposal.pdf_url
        elif format == "docx":
            export_url = f"https://api.example.com/proposals/{proposal_id}/export.docx"
        elif format == "html":
            export_url = f"https://api.example.com/proposals/{proposal_id}/export.html"
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        return {
            "proposal_id": proposal_id,
            "format": format,
            "export_url": export_url,
            "download_expires": (datetime.now() + timedelta(hours=24)).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export proposal: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for the automated proposal builder service"""
    try:
        health_status = await proposal_service.health_check()
        return health_status
    except Exception as e:
        return {
            "service": "automated_proposal_builder",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
