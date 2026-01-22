from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

from ..models import (
    ClaraPredictionModel, ClaraAlertRule, ClaraSystemMetric, ClaraIssuePrediction,
    ClaraSupportTicket, ClaraCustomerInteraction, ClaraSupportAgent
)
from ..schemas.predictive_issue_detection import (
    CreatePredictionModelRequest, UpdatePredictionModelRequest,
    CreateAlertRuleRequest, UpdateAlertRuleRequest,
    TrackSystemMetricRequest, PredictionModelResponse, AlertRuleResponse,
    SystemMetricResponse, IssuePredictionResponse, DetectionAnalyticsResponse
)
from ..database import get_clara_database
from core.config import settings
from core.integrations import IntegrationManager
from core.analytics import AnalyticsManager
# NLPUtils removed - not used


class PredictionModelType(str, Enum):
    TICKET_VOLUME = "ticket_volume"
    CUSTOMER_CHURN = "customer_churn"
    SYSTEM_PERFORMANCE = "system_performance"
    AGENT_PERFORMANCE = "agent_performance"
    SENTIMENT_ANALYSIS = "sentiment_analysis"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictiveIssueDetectionService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        self.models = {}
        self.scalers = {}
        
    async def create_prediction_model(
        self, 
        db: Session, 
        request: CreatePredictionModelRequest
    ) -> PredictionModelResponse:
        """Create a new prediction model"""
        try:
            model = ClaraPredictionModel(
                name=request.name,
                description=request.description,
                model_type=request.model_type,
                features=request.features,
                hyperparameters=request.hyperparameters,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(model)
            db.commit()
            db.refresh(model)
            
            # Initialize the model
            await self._initialize_model(model)
            
            return PredictionModelResponse(
                id=model.id,
                name=model.name,
                description=model.description,
                model_type=model.model_type,
                features=model.features,
                hyperparameters=model.hyperparameters,
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create prediction model: {str(e)}")
    
    async def get_prediction_model(
        self, 
        db: Session, 
        model_id: int
    ) -> PredictionModelResponse:
        """Get prediction model by ID"""
        model = db.query(ClaraPredictionModel).filter(ClaraPredictionModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Prediction model not found")
        
        return PredictionModelResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            model_type=model.model_type,
            features=model.features,
            hyperparameters=model.hyperparameters,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    async def list_prediction_models(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        model_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[PredictionModelResponse]:
        """List prediction models"""
        query = db.query(ClaraPredictionModel)
        
        if model_type:
            query = query.filter(ClaraPredictionModel.model_type == model_type)
        if is_active is not None:
            query = query.filter(ClaraPredictionModel.is_active == is_active)
        
        models = query.offset(skip).limit(limit).all()
        
        return [
            PredictionModelResponse(
                id=model.id,
                name=model.name,
                description=model.description,
                model_type=model.model_type,
                features=model.features,
                hyperparameters=model.hyperparameters,
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at
            ) for model in models
        ]
    
    async def update_prediction_model(
        self, 
        db: Session, 
        model_id: int, 
        request: UpdatePredictionModelRequest
    ) -> PredictionModelResponse:
        """Update prediction model"""
        model = db.query(ClaraPredictionModel).filter(ClaraPredictionModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Prediction model not found")
        
        try:
            if request.name is not None:
                model.name = request.name
            if request.description is not None:
                model.description = request.description
            if request.model_type is not None:
                model.model_type = request.model_type
            if request.features is not None:
                model.features = request.features
            if request.hyperparameters is not None:
                model.hyperparameters = request.hyperparameters
            if request.is_active is not None:
                model.is_active = request.is_active
            
            model.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(model)
            
            # Reinitialize model if needed
            if request.hyperparameters is not None:
                await self._initialize_model(model)
            
            return PredictionModelResponse(
                id=model.id,
                name=model.name,
                description=model.description,
                model_type=model.model_type,
                features=model.features,
                hyperparameters=model.hyperparameters,
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update prediction model: {str(e)}")
    
    async def delete_prediction_model(
        self, 
        db: Session, 
        model_id: int
    ) -> Dict[str, str]:
        """Delete prediction model"""
        model = db.query(ClaraPredictionModel).filter(ClaraPredictionModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Prediction model not found")
        
        try:
            # Remove from memory
            if model_id in self.models:
                del self.models[model_id]
            if model_id in self.scalers:
                del self.scalers[model_id]
            
            db.delete(model)
            db.commit()
            return {"message": "Prediction model deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete prediction model: {str(e)}")
    
    async def create_alert_rule(
        self, 
        db: Session, 
        request: CreateAlertRuleRequest
    ) -> AlertRuleResponse:
        """Create a new alert rule"""
        try:
            rule = ClaraAlertRule(
                name=request.name,
                description=request.description,
                conditions=request.conditions,
                severity=request.severity,
                actions=request.actions,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(rule)
            db.commit()
            db.refresh(rule)
            
            return AlertRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                conditions=rule.conditions,
                severity=rule.severity,
                actions=rule.actions,
                is_active=rule.is_active,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")
    
    async def get_alert_rule(
        self, 
        db: Session, 
        rule_id: int
    ) -> AlertRuleResponse:
        """Get alert rule by ID"""
        rule = db.query(ClaraAlertRule).filter(ClaraAlertRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            conditions=rule.conditions,
            severity=rule.severity,
            actions=rule.actions,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
    
    async def list_alert_rules(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        severity: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[AlertRuleResponse]:
        """List alert rules"""
        query = db.query(ClaraAlertRule)
        
        if severity:
            query = query.filter(ClaraAlertRule.severity == severity)
        if is_active is not None:
            query = query.filter(ClaraAlertRule.is_active == is_active)
        
        rules = query.offset(skip).limit(limit).all()
        
        return [
            AlertRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                conditions=rule.conditions,
                severity=rule.severity,
                actions=rule.actions,
                is_active=rule.is_active,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            ) for rule in rules
        ]
    
    async def update_alert_rule(
        self, 
        db: Session, 
        rule_id: int, 
        request: UpdateAlertRuleRequest
    ) -> AlertRuleResponse:
        """Update alert rule"""
        rule = db.query(ClaraAlertRule).filter(ClaraAlertRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        try:
            if request.name is not None:
                rule.name = request.name
            if request.description is not None:
                rule.description = request.description
            if request.conditions is not None:
                rule.conditions = request.conditions
            if request.severity is not None:
                rule.severity = request.severity
            if request.actions is not None:
                rule.actions = request.actions
            if request.is_active is not None:
                rule.is_active = request.is_active
            
            rule.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(rule)
            
            return AlertRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                conditions=rule.conditions,
                severity=rule.severity,
                actions=rule.actions,
                is_active=rule.is_active,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update alert rule: {str(e)}")
    
    async def delete_alert_rule(
        self, 
        db: Session, 
        rule_id: int
    ) -> Dict[str, str]:
        """Delete alert rule"""
        rule = db.query(ClaraAlertRule).filter(ClaraAlertRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        try:
            db.delete(rule)
            db.commit()
            return {"message": "Alert rule deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete alert rule: {str(e)}")
    
    async def track_system_metric(
        self, 
        db: Session, 
        request: TrackSystemMetricRequest
    ) -> SystemMetricResponse:
        """Track a system metric"""
        try:
            metric = ClaraSystemMetric(
                name=request.name,
                value=request.value,
                unit=request.unit,
                timestamp=request.timestamp or datetime.utcnow(),
                metadata=request.metadata,
                created_at=datetime.utcnow()
            )
            
            db.add(metric)
            db.commit()
            db.refresh(metric)
            
            # Check for anomalies
            await self._check_anomalies(db, metric)
            
            # Check alert rules
            await self._check_alert_rules(db, metric)
            
            return SystemMetricResponse(
                id=metric.id,
                name=metric.name,
                value=metric.value,
                unit=metric.unit,
                timestamp=metric.timestamp,
                metadata=metric.metadata,
                created_at=metric.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to track system metric: {str(e)}")
    
    async def get_system_metrics(
        self, 
        db: Session, 
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[SystemMetricResponse]:
        """Get system metrics for a specific metric name and time range"""
        metrics = db.query(ClaraSystemMetric).filter(
            and_(
                ClaraSystemMetric.name == metric_name,
                ClaraSystemMetric.timestamp >= start_time,
                ClaraSystemMetric.timestamp <= end_time
            )
        ).order_by(ClaraSystemMetric.timestamp.desc()).limit(limit).all()
        
        return [
            SystemMetricResponse(
                id=metric.id,
                name=metric.name,
                value=metric.value,
                unit=metric.unit,
                timestamp=metric.timestamp,
                metadata=metric.metadata,
                created_at=metric.created_at
            ) for metric in metrics
        ]
    
    async def predict_issues(
        self, 
        db: Session, 
        model_id: int,
        input_data: Dict[str, Any]
    ) -> IssuePredictionResponse:
        """Make predictions using a trained model"""
        try:
            # Get the model
            model_record = db.query(ClaraPredictionModel).filter(ClaraPredictionModel.id == model_id).first()
            if not model_record:
                raise HTTPException(status_code=404, detail="Prediction model not found")
            
            if not model_record.is_active:
                raise HTTPException(status_code=400, detail="Model is not active")
            
            # Get the model from memory
            if model_id not in self.models:
                await self._initialize_model(model_record)
            
            model = self.models[model_id]
            scaler = self.scalers.get(model_id)
            
            # Prepare input features
            features = []
            for feature in model_record.features:
                if feature in input_data:
                    features.append(input_data[feature])
                else:
                    features.append(0.0)  # Default value
            
            # Scale features if scaler exists
            if scaler:
                features = scaler.transform([features])[0]
            
            # Make prediction
            prediction = model.predict([features])[0]
            probability = model.predict_proba([features])[0].max() if hasattr(model, 'predict_proba') else None
            
            # Create prediction record
            prediction_record = ClaraIssuePrediction(
                model_id=model_id,
                input_data=input_data,
                prediction=prediction,
                probability=probability,
                created_at=datetime.utcnow()
            )
            
            db.add(prediction_record)
            db.commit()
            db.refresh(prediction_record)
            
            return IssuePredictionResponse(
                id=prediction_record.id,
                model_id=model_id,
                input_data=input_data,
                prediction=prediction,
                probability=probability,
                created_at=prediction_record.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to make prediction: {str(e)}")
    
    async def detect_anomalies(
        self, 
        db: Session, 
        metric_name: str,
        time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in system metrics"""
        try:
            # Get recent metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            metrics = await self.get_system_metrics(db, metric_name, start_time, end_time)
            
            if len(metrics) < 10:
                return []  # Need more data for anomaly detection
            
            # Extract values
            values = [m.value for m in metrics]
            
            # Use Isolation Forest for anomaly detection
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            values_2d = np.array(values).reshape(-1, 1)
            anomaly_scores = iso_forest.fit_predict(values_2d)
            
            # Find anomalies (score = -1)
            anomalies = []
            for i, score in enumerate(anomaly_scores):
                if score == -1:
                    anomalies.append({
                        "metric_name": metric_name,
                        "value": values[i],
                        "timestamp": metrics[i].timestamp,
                        "anomaly_score": abs(iso_forest.score_samples([values[i]])[0]),
                        "severity": self._calculate_anomaly_severity(values[i], values)
                    })
            
            return anomalies
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")
    
    async def analyze_trends(
        self, 
        db: Session, 
        metric_name: str,
        time_window_days: int = 7
    ) -> Dict[str, Any]:
        """Analyze trends in system metrics"""
        try:
            # Get metrics for analysis
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=time_window_days)
            
            metrics = await self.get_system_metrics(db, metric_name, start_time, end_time)
            
            if len(metrics) < 2:
                return {"error": "Insufficient data for trend analysis"}
            
            # Extract values and timestamps
            values = [m.value for m in metrics]
            timestamps = [m.timestamp for m in metrics]
            
            # Calculate basic statistics
            mean_value = np.mean(values)
            std_value = np.std(values)
            min_value = np.min(values)
            max_value = np.max(values)
            
            # Calculate trend (simple linear regression)
            x = np.array([(t - timestamps[0]).total_seconds() for t in timestamps])
            y = np.array(values)
            
            if len(x) > 1:
                slope = np.polyfit(x, y, 1)[0]
                trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
                trend_strength = abs(slope)
            else:
                trend_direction = "stable"
                trend_strength = 0
            
            # Detect seasonality (simple approach)
            if len(values) >= 24:  # At least 24 data points
                # Check for daily patterns
                hourly_values = {}
                for i, timestamp in enumerate(timestamps):
                    hour = timestamp.hour
                    if hour not in hourly_values:
                        hourly_values[hour] = []
                    hourly_values[hour].append(values[i])
                
                hourly_means = {hour: np.mean(vals) for hour, vals in hourly_values.items()}
                seasonality_score = np.std(list(hourly_means.values())) / mean_value if mean_value > 0 else 0
            else:
                seasonality_score = 0
            
            return {
                "metric_name": metric_name,
                "time_window_days": time_window_days,
                "data_points": len(values),
                "statistics": {
                    "mean": mean_value,
                    "std": std_value,
                    "min": min_value,
                    "max": max_value
                },
                "trend": {
                    "direction": trend_direction,
                    "strength": trend_strength
                },
                "seasonality": {
                    "score": seasonality_score,
                    "has_pattern": seasonality_score > 0.1
                },
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to analyze trends: {str(e)}")
    
    async def train_model(
        self, 
        db: Session, 
        model_id: int,
        training_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Train a prediction model"""
        try:
            # Get the model
            model_record = db.query(ClaraPredictionModel).filter(ClaraPredictionModel.id == model_id).first()
            if not model_record:
                raise HTTPException(status_code=404, detail="Prediction model not found")
            
            if len(training_data) < 10:
                raise HTTPException(status_code=400, detail="Insufficient training data")
            
            # Prepare training data
            X = []
            y = []
            
            for data_point in training_data:
                features = []
                for feature in model_record.features:
                    if feature in data_point:
                        features.append(data_point[feature])
                    else:
                        features.append(0.0)
                
                X.append(features)
                y.append(data_point.get('target', 0))
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                **model_record.hyperparameters
            )
            model.fit(X_scaled, y)
            
            # Store model and scaler
            self.models[model_id] = model
            self.scalers[model_id] = scaler
            
            # Calculate training metrics
            train_score = model.score(X_scaled, y)
            
            return {
                "model_id": model_id,
                "training_samples": len(training_data),
                "training_score": train_score,
                "model_type": model_record.model_type,
                "features_used": model_record.features,
                "training_completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to train model: {str(e)}")
    
    async def evaluate_model(
        self, 
        db: Session, 
        model_id: int,
        test_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate a trained model"""
        try:
            # Get the model
            model_record = db.query(ClaraPredictionModel).filter(ClaraPredictionModel.id == model_id).first()
            if not model_record:
                raise HTTPException(status_code=404, detail="Prediction model not found")
            
            if model_id not in self.models:
                raise HTTPException(status_code=400, detail="Model not trained")
            
            model = self.models[model_id]
            scaler = self.scalers[model_id]
            
            # Prepare test data
            X_test = []
            y_test = []
            
            for data_point in test_data:
                features = []
                for feature in model_record.features:
                    if feature in data_point:
                        features.append(data_point[feature])
                    else:
                        features.append(0.0)
                
                X_test.append(features)
                y_test.append(data_point.get('target', 0))
            
            # Scale features
            X_test_scaled = scaler.transform(X_test)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled) if hasattr(model, 'predict_proba') else None
            
            # Calculate metrics
            accuracy = np.mean(y_pred == y_test)
            
            # Calculate additional metrics for classification
            if model_record.model_type in ["customer_churn", "sentiment_analysis"]:
                from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
                
                precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
                conf_matrix = confusion_matrix(y_test, y_pred).tolist()
                
                metrics = {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "confusion_matrix": conf_matrix
                }
            else:
                # For regression models
                from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
                
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                metrics = {
                    "accuracy": accuracy,
                    "mse": mse,
                    "mae": mae,
                    "r2_score": r2
                }
            
            return {
                "model_id": model_id,
                "test_samples": len(test_data),
                "metrics": metrics,
                "evaluation_completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to evaluate model: {str(e)}")
    
    async def get_detection_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime
    ) -> DetectionAnalyticsResponse:
        """Get comprehensive detection analytics"""
        try:
            # Get predictions in date range
            predictions = db.query(ClaraIssuePrediction).filter(
                and_(
                    ClaraIssuePrediction.created_at >= start_date,
                    ClaraIssuePrediction.created_at <= end_date
                )
            ).all()
            
            # Get system metrics in date range
            metrics = db.query(ClaraSystemMetric).filter(
                and_(
                    ClaraSystemMetric.created_at >= start_date,
                    ClaraSystemMetric.created_at <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_predictions = len(predictions)
            total_metrics = len(metrics)
            
            # Model performance
            model_performance = {}
            for prediction in predictions:
                model_id = prediction.model_id
                if model_id not in model_performance:
                    model_performance[model_id] = {"total": 0, "high_probability": 0}
                model_performance[model_id]["total"] += 1
                if prediction.probability and prediction.probability > 0.8:
                    model_performance[model_id]["high_probability"] += 1
            
            # Metric statistics
            metric_stats = {}
            for metric in metrics:
                name = metric.name
                if name not in metric_stats:
                    metric_stats[name] = {"count": 0, "values": []}
                metric_stats[name]["count"] += 1
                metric_stats[name]["values"].append(metric.value)
            
            # Calculate averages
            for name in metric_stats:
                values = metric_stats[name]["values"]
                metric_stats[name]["average"] = np.mean(values)
                metric_stats[name]["std"] = np.std(values)
                del metric_stats[name]["values"]  # Remove raw values to reduce response size
            
            return DetectionAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_predictions=total_predictions,
                total_metrics=total_metrics,
                model_performance=model_performance,
                metric_statistics=metric_stats
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get detection analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of predictive issue detection system"""
        try:
            db = next(get_db())
            model_count = db.query(ClaraPredictionModel).count()
            rule_count = db.query(ClaraAlertRule).count()
            metric_count = db.query(ClaraSystemMetric).count()
            prediction_count = db.query(ClaraIssuePrediction).count()
            
            # Check model status
            active_models = db.query(ClaraPredictionModel).filter(ClaraPredictionModel.is_active == True).count()
            trained_models = len(self.models)
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "models_count": model_count,
                    "rules_count": rule_count,
                    "metrics_count": metric_count,
                    "predictions_count": prediction_count
                },
                "models": {
                    "active_models": active_models,
                    "trained_models": trained_models,
                    "models_in_memory": list(self.models.keys())
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _initialize_model(self, model_record: ClaraPredictionModel):
        """Initialize a prediction model"""
        try:
            if model_record.model_type == PredictionModelType.TICKET_VOLUME:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_record.model_type == PredictionModelType.CUSTOMER_CHURN:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_record.model_type == PredictionModelType.SYSTEM_PERFORMANCE:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_record.model_type == PredictionModelType.AGENT_PERFORMANCE:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_record.model_type == PredictionModelType.SENTIMENT_ANALYSIS:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Apply hyperparameters
            if model_record.hyperparameters:
                model.set_params(**model_record.hyperparameters)
            
            self.models[model_record.id] = model
            self.scalers[model_record.id] = StandardScaler()
            
        except Exception as e:
            raise Exception(f"Failed to initialize model: {str(e)}")
    
    async def _check_anomalies(self, db: Session, metric: ClaraSystemMetric):
        """Check for anomalies in a metric"""
        try:
            # Get recent metrics of the same type
            recent_metrics = db.query(ClaraSystemMetric).filter(
                and_(
                    ClaraSystemMetric.name == metric.name,
                    ClaraSystemMetric.timestamp >= metric.timestamp - timedelta(hours=1)
                )
            ).all()
            
            if len(recent_metrics) < 5:
                return  # Need more data
            
            values = [m.value for m in recent_metrics]
            current_value = metric.value
            
            # Simple anomaly detection using z-score
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val > 0:
                z_score = abs(current_value - mean_val) / std_val
                if z_score > 3:  # Anomaly threshold
                    # Log anomaly
                    await self._log_detection_event("anomaly_detected", {
                        "metric_name": metric.name,
                        "value": current_value,
                        "z_score": z_score,
                        "timestamp": metric.timestamp.isoformat()
                    })
                    
        except Exception:
            pass  # Silently fail anomaly detection
    
    async def _check_alert_rules(self, db: Session, metric: ClaraSystemMetric):
        """Check alert rules against a metric"""
        try:
            # Get active alert rules
            rules = db.query(ClaraAlertRule).filter(ClaraAlertRule.is_active == True).all()
            
            for rule in rules:
                if self._evaluate_rule_conditions(rule.conditions, metric):
                    # Trigger alert
                    await self._trigger_alert(rule, metric)
                    
        except Exception:
            pass  # Silently fail alert checking
    
    def _evaluate_rule_conditions(self, conditions: Dict[str, Any], metric: ClaraSystemMetric) -> bool:
        """Evaluate alert rule conditions"""
        try:
            if "metric_name" in conditions and conditions["metric_name"] != metric.name:
                return False
            
            if "threshold" in conditions:
                operator = conditions.get("operator", ">")
                threshold = conditions["threshold"]
                
                if operator == ">":
                    return metric.value > threshold
                elif operator == "<":
                    return metric.value < threshold
                elif operator == ">=":
                    return metric.value >= threshold
                elif operator == "<=":
                    return metric.value <= threshold
                elif operator == "==":
                    return metric.value == threshold
            
            return False
            
        except Exception:
            return False
    
    async def _trigger_alert(self, rule: ClaraAlertRule, metric: ClaraSystemMetric):
        """Trigger an alert"""
        try:
            alert_data = {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "severity": rule.severity,
                "metric_name": metric.name,
                "metric_value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "actions": rule.actions
            }
            
            # Log alert
            await self._log_detection_event("alert_triggered", alert_data)
            
            # Execute alert actions
            for action in rule.actions:
                await self._execute_alert_action(action, alert_data)
                
        except Exception:
            pass  # Silently fail alert triggering
    
    async def _execute_alert_action(self, action: Dict[str, Any], alert_data: Dict[str, Any]):
        """Execute an alert action"""
        try:
            action_type = action.get("type")
            
            if action_type == "email":
                await self.integration_manager.send_email({
                    "to": action.get("recipients", []),
                    "subject": f"Alert: {alert_data['rule_name']}",
                    "content": f"Alert triggered for {alert_data['metric_name']} with value {alert_data['metric_value']}"
                })
            elif action_type == "slack":
                await self.integration_manager.send_slack_message({
                    "channel": action.get("channel", "#alerts"),
                    "text": f"🚨 Alert: {alert_data['rule_name']} - {alert_data['metric_name']}: {alert_data['metric_value']}"
                })
            elif action_type == "webhook":
                await self.integration_manager.send_webhook({
                    "url": action.get("url"),
                    "data": alert_data
                })
                
        except Exception:
            pass  # Silently fail action execution
    
    def _calculate_anomaly_severity(self, value: float, all_values: List[float]) -> str:
        """Calculate anomaly severity"""
        try:
            mean_val = np.mean(all_values)
            std_val = np.std(all_values)
            
            if std_val == 0:
                return AlertSeverity.LOW
            
            z_score = abs(value - mean_val) / std_val
            
            if z_score > 5:
                return AlertSeverity.CRITICAL
            elif z_score > 4:
                return AlertSeverity.HIGH
            elif z_score > 3:
                return AlertSeverity.MEDIUM
            else:
                return AlertSeverity.LOW
                
        except Exception:
            return AlertSeverity.LOW
    
    async def _log_detection_event(self, event_type: str, data: Dict[str, Any]):
        """Log detection events for analytics"""
        try:
            log_data = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            await self.analytics_manager.log_event("predictive_issue_detection", log_data)
            
        except Exception:
            pass
