from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityBusinessIdea, PurityBusinessHealth, PurityBusinessModel, PurityFinancialForecast
from ..services.business_health_service import BusinessHealthService

router = APIRouter(prefix="/business-health", tags=["Business Health"])

class BusinessHealthRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    current_revenue: float = Field(..., ge=0, description="Current monthly revenue")
    current_costs: float = Field(..., ge=0, description="Current monthly costs")
    customer_count: int = Field(..., ge=0, description="Total number of customers")
    conversion_rate: float = Field(..., ge=0, le=100, description="Conversion rate percentage")
    churn_rate: float = Field(..., ge=0, le=100, description="Customer churn rate percentage")
    growth_rate: float = Field(..., description="Monthly growth rate percentage")

class KPITrackingRequest(BaseModel):
    business_health_id: int = Field(..., description="Business health ID")
    metrics_data: Dict[str, Any] = Field(..., description="KPI metrics data")
    tracking_period: str = Field(..., description="Tracking period (weekly, monthly, quarterly)")

class HealthReportRequest(BaseModel):
    business_health_id: int = Field(..., description="Business health ID")
    report_type: str = Field(..., description="Type of health report")
    include_recommendations: bool = Field(True, description="Include improvement recommendations")

class HealthUpdateRequest(BaseModel):
    health_id: int = Field(..., description="Health record ID")
    current_revenue: float = Field(..., ge=0, description="Updated current revenue")
    current_costs: float = Field(..., ge=0, description="Updated current costs")
    customer_count: int = Field(..., ge=0, description="Updated customer count")
    conversion_rate: float = Field(..., ge=0, le=100, description="Updated conversion rate")
    churn_rate: float = Field(..., ge=0, le=100, description="Updated churn rate")
    growth_rate: float = Field(..., description="Updated growth rate")

@router.post("/dashboard")
async def create_business_health_dashboard(
    request: BusinessHealthRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a comprehensive business health dashboard"""
    try:
        service = BusinessHealthService()
        result = await service.create_business_health_dashboard(
            db=db,
            business_idea_id=request.business_idea_id,
            current_revenue=request.current_revenue,
            current_costs=request.current_costs,
            customer_count=request.customer_count,
            conversion_rate=request.conversion_rate,
            churn_rate=request.churn_rate,
            growth_rate=request.growth_rate
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Business health dashboard created with score: {result.health_score}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create business health dashboard: {str(e)}"
        )

@router.post("/track-kpi")
async def track_kpi_metrics(
    request: KPITrackingRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Track KPI metrics and analyze performance trends"""
    try:
        service = BusinessHealthService()
        result = await service.track_kpi_metrics(
            db=db,
            business_health_id=request.business_health_id,
            metrics_data=request.metrics_data,
            tracking_period=request.tracking_period
        )
        return {
            "status": "success",
            "data": result,
            "message": f"KPI metrics tracked for {request.tracking_period} period"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track KPI metrics: {str(e)}"
        )

@router.post("/health-report")
async def generate_health_report(
    request: HealthReportRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate a comprehensive business health report"""
    try:
        service = BusinessHealthService()
        result = await service.generate_health_report(
            db=db,
            business_health_id=request.business_health_id,
            report_type=request.report_type,
            include_recommendations=request.include_recommendations
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Health report generated for {request.report_type} analysis"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate health report: {str(e)}"
        )

@router.put("/update")
async def update_business_health(
    request: HealthUpdateRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Update business health metrics and recalculate health score"""
    try:
        service = BusinessHealthService()
        result = await service.update_business_health(
            db=db,
            health_id=request.health_id,
            current_revenue=request.current_revenue,
            current_costs=request.current_costs,
            customer_count=request.customer_count,
            conversion_rate=request.conversion_rate,
            churn_rate=request.churn_rate,
            growth_rate=request.growth_rate
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Business health updated with new score: {result.health_score}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update business health: {str(e)}"
        )

@router.get("/health-metrics")
async def get_health_metrics(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get business health metrics and scoring criteria"""
    try:
        metrics = {
            "financial_health_weights": {
                "revenue_growth": 0.25,
                "profit_margin": 0.20,
                "cash_flow": 0.20,
                "cost_efficiency": 0.15,
                "financial_stability": 0.20
            },
            "operational_health_weights": {
                "customer_satisfaction": 0.30,
                "operational_efficiency": 0.25,
                "process_optimization": 0.20,
                "quality_metrics": 0.15,
                "scalability": 0.10
            },
            "customer_health_weights": {
                "customer_acquisition": 0.25,
                "customer_retention": 0.30,
                "customer_lifetime_value": 0.25,
                "customer_satisfaction": 0.20
            },
            "growth_health_weights": {
                "market_expansion": 0.30,
                "product_development": 0.25,
                "team_growth": 0.20,
                "innovation_rate": 0.25
            },
            "scoring_criteria": {
                "excellent": "90-100",
                "good": "75-89",
                "fair": "60-74",
                "poor": "Below 60"
            }
        }
        return {
            "status": "success",
            "data": metrics,
            "message": "Health metrics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health metrics: {str(e)}"
        )

@router.get("/kpi-templates")
async def get_kpi_templates(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get KPI templates for different business types"""
    try:
        kpi_templates = {
            "saas_business": {
                "name": "SaaS Business KPIs",
                "financial_kpis": [
                    "Monthly Recurring Revenue (MRR)",
                    "Annual Recurring Revenue (ARR)",
                    "Customer Acquisition Cost (CAC)",
                    "Lifetime Value (LTV)",
                    "LTV/CAC Ratio",
                    "Churn Rate",
                    "Net Revenue Retention"
                ],
                "operational_kpis": [
                    "Customer Satisfaction Score (CSAT)",
                    "Net Promoter Score (NPS)",
                    "Support Ticket Resolution Time",
                    "Feature Adoption Rate",
                    "System Uptime"
                ],
                "growth_kpis": [
                    "New Customer Growth Rate",
                    "Revenue Growth Rate",
                    "Market Share",
                    "Product Usage Metrics",
                    "Expansion Revenue"
                ]
            },
            "ecommerce_business": {
                "name": "E-commerce Business KPIs",
                "financial_kpis": [
                    "Gross Merchandise Value (GMV)",
                    "Average Order Value (AOV)",
                    "Customer Acquisition Cost (CAC)",
                    "Customer Lifetime Value (CLV)",
                    "Conversion Rate",
                    "Return Rate",
                    "Profit Margins"
                ],
                "operational_kpis": [
                    "Order Fulfillment Time",
                    "Inventory Turnover",
                    "Customer Satisfaction",
                    "Return Processing Time",
                    "Website Performance"
                ],
                "growth_kpis": [
                    "Traffic Growth",
                    "Revenue Growth",
                    "Customer Growth",
                    "Market Expansion",
                    "Product Performance"
                ]
            },
            "service_business": {
                "name": "Service Business KPIs",
                "financial_kpis": [
                    "Revenue per Client",
                    "Profit Margins",
                    "Client Acquisition Cost",
                    "Client Lifetime Value",
                    "Utilization Rate",
                    "Billable Hours",
                    "Cash Flow"
                ],
                "operational_kpis": [
                    "Client Satisfaction",
                    "Project Completion Rate",
                    "Service Quality Metrics",
                    "Team Productivity",
                    "Response Time"
                ],
                "growth_kpis": [
                    "Client Growth Rate",
                    "Revenue Growth",
                    "Service Expansion",
                    "Market Penetration",
                    "Referral Rate"
                ]
            },
            "manufacturing_business": {
                "name": "Manufacturing Business KPIs",
                "financial_kpis": [
                    "Revenue per Unit",
                    "Cost of Goods Sold",
                    "Gross Profit Margin",
                    "Inventory Turnover",
                    "Production Efficiency",
                    "Quality Costs",
                    "Cash Conversion Cycle"
                ],
                "operational_kpis": [
                    "Production Yield",
                    "Equipment Efficiency",
                    "Quality Metrics",
                    "Lead Time",
                    "Safety Incidents"
                ],
                "growth_kpis": [
                    "Production Volume Growth",
                    "Market Share",
                    "New Product Development",
                    "Capacity Utilization",
                    "Export Growth"
                ]
            }
        }
        return {
            "status": "success",
            "data": kpi_templates,
            "message": "KPI templates retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve KPI templates: {str(e)}"
        )

@router.get("/health-benchmarks")
async def get_health_benchmarks(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get industry benchmarks for business health metrics"""
    try:
        benchmarks = {
            "saas_benchmarks": {
                "name": "SaaS Industry Benchmarks",
                "financial_metrics": {
                    "monthly_churn_rate": {
                        "excellent": "< 2%",
                        "good": "2-5%",
                        "fair": "5-10%",
                        "poor": "> 10%"
                    },
                    "ltv_cac_ratio": {
                        "excellent": "> 5:1",
                        "good": "3:1 - 5:1",
                        "fair": "2:1 - 3:1",
                        "poor": "< 2:1"
                    },
                    "net_revenue_retention": {
                        "excellent": "> 120%",
                        "good": "110-120%",
                        "fair": "100-110%",
                        "poor": "< 100%"
                    }
                },
                "operational_metrics": {
                    "customer_satisfaction": {
                        "excellent": "> 90%",
                        "good": "80-90%",
                        "fair": "70-80%",
                        "poor": "< 70%"
                    },
                    "response_time": {
                        "excellent": "< 2 hours",
                        "good": "2-8 hours",
                        "fair": "8-24 hours",
                        "poor": "> 24 hours"
                    }
                }
            },
            "ecommerce_benchmarks": {
                "name": "E-commerce Industry Benchmarks",
                "financial_metrics": {
                    "conversion_rate": {
                        "excellent": "> 5%",
                        "good": "3-5%",
                        "fair": "1-3%",
                        "poor": "< 1%"
                    },
                    "average_order_value": {
                        "excellent": "> $100",
                        "good": "$50-$100",
                        "fair": "$25-$50",
                        "poor": "< $25"
                    },
                    "customer_lifetime_value": {
                        "excellent": "> $500",
                        "good": "$200-$500",
                        "fair": "$100-$200",
                        "poor": "< $100"
                    }
                },
                "operational_metrics": {
                    "order_fulfillment_time": {
                        "excellent": "< 24 hours",
                        "good": "1-3 days",
                        "fair": "3-7 days",
                        "poor": "> 7 days"
                    },
                    "return_rate": {
                        "excellent": "< 5%",
                        "good": "5-10%",
                        "fair": "10-20%",
                        "poor": "> 20%"
                    }
                }
            },
            "service_benchmarks": {
                "name": "Service Industry Benchmarks",
                "financial_metrics": {
                    "utilization_rate": {
                        "excellent": "> 85%",
                        "good": "75-85%",
                        "fair": "65-75%",
                        "poor": "< 65%"
                    },
                    "profit_margin": {
                        "excellent": "> 25%",
                        "good": "15-25%",
                        "fair": "10-15%",
                        "poor": "< 10%"
                    },
                    "client_retention": {
                        "excellent": "> 95%",
                        "good": "85-95%",
                        "fair": "75-85%",
                        "poor": "< 75%"
                    }
                },
                "operational_metrics": {
                    "project_completion_rate": {
                        "excellent": "> 95%",
                        "good": "90-95%",
                        "fair": "85-90%",
                        "poor": "< 85%"
                    },
                    "client_satisfaction": {
                        "excellent": "> 90%",
                        "good": "80-90%",
                        "fair": "70-80%",
                        "poor": "< 70%"
                    }
                }
            }
        }
        return {
            "status": "success",
            "data": benchmarks,
            "message": "Health benchmarks retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health benchmarks: {str(e)}"
        )
