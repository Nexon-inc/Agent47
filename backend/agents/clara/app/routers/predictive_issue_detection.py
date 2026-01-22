from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..services.predictive_issue_detection_service import PredictiveIssueDetectionService
from ..models import ClaraIssuePrediction, ClaraPredictionModel, ClaraSystemMetric, ClaraAlertRule, ClaraIssuePattern
from ..core.integration_manager import IntegrationManager
from ..core.event_bus import EventBus

router = APIRouter()

# Pydantic models for request/response
class CreatePredictionModelRequest(BaseModel):
    model_name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type (anomaly_detection, trend_analysis, pattern_recognition)")
    target_metric: str = Field(..., description="Target metric to predict")
    features: List[str] = Field(..., description="Input features for the model")
    algorithm: str = Field(..., description="ML algorithm to use")
    parameters: Dict[str, Any] = Field(..., description="Model parameters")
    is_active: bool = Field(True, description="Model active status")

class UpdatePredictionModelRequest(BaseModel):
    model_name: Optional[str] = Field(None, description="Model name")
    model_type: Optional[str] = Field(None, description="Model type")
    target_metric: Optional[str] = Field(None, description="Target metric")
    features: Optional[List[str]] = Field(None, description="Input features")
    algorithm: Optional[str] = Field(None, description="ML algorithm")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Model parameters")
    is_active: Optional[bool] = Field(None, description="Model active status")

class CreateAlertRuleRequest(BaseModel):
    rule_name: str = Field(..., description="Rule name")
    rule_type: str = Field(..., description="Rule type (threshold, anomaly, trend)")
    metric_name: str = Field(..., description="Metric to monitor")
    condition: str = Field(..., description="Alert condition")
    threshold_value: float = Field(..., description="Threshold value")
    severity: str = Field(..., description="Alert severity (low, medium, high, critical)")
    notification_channels: List[str] = Field(..., description="Notification channels")
    is_active: bool = Field(True, description="Rule active status")

class UpdateAlertRuleRequest(BaseModel):
    rule_name: Optional[str] = Field(None, description="Rule name")
    rule_type: Optional[str] = Field(None, description="Rule type")
    metric_name: Optional[str] = Field(None, description="Metric to monitor")
    condition: Optional[str] = Field(None, description="Alert condition")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    severity: Optional[str] = Field(None, description="Alert severity")
    notification_channels: Optional[List[str]] = Field(None, description="Notification channels")
    is_active: Optional[bool] = Field(None, description="Rule active status")

class SystemMetricData(BaseModel):
    metric_name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(..., description="Metric timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class PredictionModelResponse(BaseModel):
    id: int
    model_name: str
    model_type: str
    target_metric: str
    features: List[str]
    algorithm: str
    parameters: Dict[str, Any]
    is_active: bool
    accuracy: Optional[float]
    last_trained: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AlertRuleResponse(BaseModel):
    id: int
    rule_name: str
    rule_type: str
    metric_name: str
    condition: str
    threshold_value: float
    severity: str
    notification_channels: List[str]
    is_active: bool
    alert_count: int
    last_triggered: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IssuePredictionResponse(BaseModel):
    id: int
    prediction_type: str
    metric_name: str
    predicted_value: float
    confidence_score: float
    prediction_horizon: int
    severity: str
    description: str
    recommended_actions: List[str]
    predicted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class SystemMetricResponse(BaseModel):
    id: int
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class IssuePatternResponse(BaseModel):
    id: int
    pattern_name: str
    pattern_type: str
    description: str
    indicators: List[str]
    confidence_score: float
    frequency: int
    impact_level: str
    mitigation_strategies: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PredictionAnalyticsResponse(BaseModel):
    total_predictions: int
    accurate_predictions: int
    false_positives: int
    false_negatives: int
    accuracy_rate: float
    precision_rate: float
    recall_rate: float
    f1_score: float
    top_models: List[Dict[str, Any]]
    prediction_trends: List[Dict[str, Any]]

# Dependency
async def get_predictive_issue_detection_service(db: AsyncSession = Depends(get_db)) -> PredictiveIssueDetectionService:
    integration_manager = IntegrationManager()
    event_bus = EventBus()
    return PredictiveIssueDetectionService(db, integration_manager, event_bus)

# Prediction Model Management
@router.post("/models", response_model=PredictionModelResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction_model(
    request: CreatePredictionModelRequest,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Create a new prediction model"""
    try:
        model = await service.create_prediction_model(
            model_name=request.model_name,
            model_type=request.model_type,
            target_metric=request.target_metric,
            features=request.features,
            algorithm=request.algorithm,
            parameters=request.parameters,
            is_active=request.is_active
        )
        return PredictionModelResponse.from_orm(model)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/models", response_model=List[PredictionModelResponse])
async def get_prediction_models(
    model_type: Optional[str] = None,
    target_metric: Optional[str] = None,
    active_only: bool = True,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get prediction models with optional filtering"""
    try:
        models = await service.get_prediction_models(
            model_type=model_type,
            target_metric=target_metric,
            active_only=active_only
        )
        return [PredictionModelResponse.from_orm(model) for model in models]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/models/{model_id}", response_model=PredictionModelResponse)
async def get_prediction_model(
    model_id: int,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get a specific prediction model by ID"""
    try:
        model = await service.get_prediction_model(model_id)
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction model not found")
        return PredictionModelResponse.from_orm(model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/models/{model_id}", response_model=PredictionModelResponse)
async def update_prediction_model(
    model_id: int,
    request: UpdatePredictionModelRequest,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Update a prediction model"""
    try:
        model = await service.update_prediction_model(
            model_id=model_id,
            model_name=request.model_name,
            model_type=request.model_type,
            target_metric=request.target_metric,
            features=request.features,
            algorithm=request.algorithm,
            parameters=request.parameters,
            is_active=request.is_active
        )
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction model not found")
        return PredictionModelResponse.from_orm(model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prediction_model(
    model_id: int,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Delete a prediction model"""
    try:
        success = await service.delete_prediction_model(model_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction model not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Alert Rule Management
@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    request: CreateAlertRuleRequest,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Create a new alert rule"""
    try:
        rule = await service.create_alert_rule(
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            metric_name=request.metric_name,
            condition=request.condition,
            threshold_value=request.threshold_value,
            severity=request.severity,
            notification_channels=request.notification_channels,
            is_active=request.is_active
        )
        return AlertRuleResponse.from_orm(rule)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/alert-rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    rule_type: Optional[str] = None,
    metric_name: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get alert rules with optional filtering"""
    try:
        rules = await service.get_alert_rules(
            rule_type=rule_type,
            metric_name=metric_name,
            severity=severity,
            active_only=active_only
        )
        return [AlertRuleResponse.from_orm(rule) for rule in rules]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get a specific alert rule by ID"""
    try:
        rule = await service.get_alert_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
        return AlertRuleResponse.from_orm(rule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    request: UpdateAlertRuleRequest,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Update an alert rule"""
    try:
        rule = await service.update_alert_rule(
            rule_id=rule_id,
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            metric_name=request.metric_name,
            condition=request.condition,
            threshold_value=request.threshold_value,
            severity=request.severity,
            notification_channels=request.notification_channels,
            is_active=request.is_active
        )
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
        return AlertRuleResponse.from_orm(rule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/alert-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: int,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Delete an alert rule"""
    try:
        success = await service.delete_alert_rule(rule_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# System Metrics Management
@router.post("/metrics", response_model=SystemMetricResponse, status_code=status.HTTP_201_CREATED)
async def record_system_metric(
    metric_data: SystemMetricData,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Record a system metric"""
    try:
        metric = await service.record_system_metric(
            metric_name=metric_data.metric_name,
            value=metric_data.value,
            timestamp=metric_data.timestamp,
            metadata=metric_data.metadata
        )
        return SystemMetricResponse.from_orm(metric)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/metrics/batch", response_model=List[SystemMetricResponse])
async def record_batch_metrics(
    metrics_data: List[SystemMetricData],
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Record multiple system metrics in batch"""
    try:
        metrics = await service.record_batch_metrics(metrics_data)
        return [SystemMetricResponse.from_orm(metric) for metric in metrics]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/metrics", response_model=List[SystemMetricResponse])
async def get_system_metrics(
    metric_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get system metrics with optional filtering"""
    try:
        metrics = await service.get_system_metrics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return [SystemMetricResponse.from_orm(metric) for metric in metrics]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Issue Prediction and Detection
@router.post("/predict")
async def generate_predictions(
    target_metric: str,
    prediction_horizon: int = 24,
    confidence_threshold: float = 0.7,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Generate predictions for a specific metric"""
    try:
        predictions = await service.generate_predictions(
            target_metric=target_metric,
            prediction_horizon=prediction_horizon,
            confidence_threshold=confidence_threshold
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/predictions", response_model=List[IssuePredictionResponse])
async def get_issue_predictions(
    prediction_type: Optional[str] = None,
    metric_name: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get issue predictions with optional filtering"""
    try:
        predictions = await service.get_issue_predictions(
            prediction_type=prediction_type,
            metric_name=metric_name,
            severity=severity,
            start_date=start_date,
            end_date=end_date
        )
        return [IssuePredictionResponse.from_orm(prediction) for prediction in predictions]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/predictions/{prediction_id}", response_model=IssuePredictionResponse)
async def get_issue_prediction(
    prediction_id: int,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get a specific issue prediction by ID"""
    try:
        prediction = await service.get_issue_prediction(prediction_id)
        if not prediction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue prediction not found")
        return IssuePredictionResponse.from_orm(prediction)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Anomaly Detection
@router.post("/detect-anomalies")
async def detect_anomalies(
    metric_name: str,
    time_window: int = 24,
    sensitivity: float = 0.8,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Detect anomalies in system metrics"""
    try:
        anomalies = await service.detect_anomalies(
            metric_name=metric_name,
            time_window=time_window,
            sensitivity=sensitivity
        )
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/detect-trends")
async def detect_trends(
    metric_name: str,
    trend_type: str = "all",
    time_window: int = 168,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Detect trends in system metrics"""
    try:
        trends = await service.detect_trends(
            metric_name=metric_name,
            trend_type=trend_type,
            time_window=time_window
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Pattern Recognition
@router.get("/patterns", response_model=List[IssuePatternResponse])
async def get_issue_patterns(
    pattern_type: Optional[str] = None,
    impact_level: Optional[str] = None,
    min_confidence: float = 0.5,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get recognized issue patterns"""
    try:
        patterns = await service.get_issue_patterns(
            pattern_type=pattern_type,
            impact_level=impact_level,
            min_confidence=min_confidence
        )
        return [IssuePatternResponse.from_orm(pattern) for pattern in patterns]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/patterns/analyze")
async def analyze_patterns(
    time_window: int = 168,
    min_frequency: int = 3,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Analyze and discover new patterns"""
    try:
        analysis_results = await service.analyze_patterns(
            time_window=time_window,
            min_frequency=min_frequency
        )
        return analysis_results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Early Warning System
@router.post("/early-warnings")
async def generate_early_warnings(
    warning_type: str = "all",
    severity_threshold: str = "medium",
    time_horizon: int = 48,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Generate early warning alerts"""
    try:
        warnings = await service.generate_early_warnings(
            warning_type=warning_type,
            severity_threshold=severity_threshold,
            time_horizon=time_horizon
        )
        return warnings
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/early-warnings", response_model=List[Dict[str, Any]])
async def get_early_warnings(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get early warning alerts"""
    try:
        warnings = await service.get_early_warnings(
            status=status,
            severity=severity,
            start_date=start_date,
            end_date=end_date
        )
        return warnings
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Model Training and Evaluation
@router.post("/models/{model_id}/train")
async def train_prediction_model(
    model_id: int,
    training_data_start: Optional[datetime] = None,
    training_data_end: Optional[datetime] = None,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Train a prediction model"""
    try:
        training_results = await service.train_prediction_model(
            model_id=model_id,
            training_data_start=training_data_start,
            training_data_end=training_data_end
        )
        return training_results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/models/{model_id}/evaluate")
async def evaluate_prediction_model(
    model_id: int,
    test_data_start: Optional[datetime] = None,
    test_data_end: Optional[datetime] = None,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Evaluate a prediction model"""
    try:
        evaluation_results = await service.evaluate_prediction_model(
            model_id=model_id,
            test_data_start=test_data_start,
            test_data_end=test_data_end
        )
        return evaluation_results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Analytics and Reporting
@router.get("/analytics", response_model=PredictionAnalyticsResponse)
async def get_prediction_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    model_id: Optional[int] = None,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get prediction analytics and performance metrics"""
    try:
        analytics = await service.get_prediction_analytics(
            start_date=start_date,
            end_date=end_date,
            model_id=model_id
        )
        return PredictionAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/accuracy")
async def get_model_accuracy(
    model_id: Optional[int] = None,
    time_period: str = "30d",
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get model accuracy metrics"""
    try:
        accuracy_metrics = await service.get_model_accuracy(
            model_id=model_id,
            time_period=time_period
        )
        return accuracy_metrics
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/performance")
async def get_system_performance(
    metrics: List[str],
    time_window: int = 24,
    service: PredictiveIssueDetectionService = Depends(get_predictive_issue_detection_service)
):
    """Get system performance metrics"""
    try:
        performance_metrics = await service.get_system_performance(
            metrics=metrics,
            time_window=time_window
        )
        return performance_metrics
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint for Predictive Issue Detection"""
    return {
        "status": "healthy",
        "service": "Predictive Issue Detection",
        "features": [
            "prediction_model_management",
            "alert_rule_management",
            "system_metrics_tracking",
            "issue_prediction",
            "anomaly_detection",
            "trend_analysis",
            "pattern_recognition",
            "early_warning_system",
            "model_training_evaluation",
            "prediction_analytics"
        ],
        "message": "Predictive Issue Detection service is running and ready!"
    }
