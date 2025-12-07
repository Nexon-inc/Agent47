import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from backend.core.config import settings

logger = logging.getLogger(__name__)

class DataProcessor:
    """Data processing utilities for Joe research agent"""
    
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'xlsx', 'xml']
        
    def clean_research_data(self, data: Union[List[Dict], pd.DataFrame], data_type: str) -> Dict[str, Any]:
        """Clean and validate research data"""
        try:
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                return {"success": False, "error": "Unsupported data format"}
            
            # Remove duplicates
            initial_count = len(df)
            df = df.drop_duplicates()
            duplicates_removed = initial_count - len(df)
            
            # Remove null values
            null_counts = df.isnull().sum().to_dict()
            df = df.dropna()
            
            # Basic data validation
            validation_results = {
                "total_records": len(df),
                "duplicates_removed": duplicates_removed,
                "null_values_removed": null_counts,
                "data_type": data_type,
                "cleaned_data": df.to_dict('records')
            }
            
            return {"success": True, "results": validation_results}
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            return {"success": False, "error": str(e)}
    
    def aggregate_research_data(self, data: List[Dict], aggregation_type: str, group_by: str = None) -> Dict[str, Any]:
        """Aggregate research data based on specified criteria"""
        try:
            df = pd.DataFrame(data)
            
            if group_by and group_by in df.columns:
                if aggregation_type == "count":
                    result = df.groupby(group_by).size().to_dict()
                elif aggregation_type == "sum":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    result = df.groupby(group_by)[numeric_cols].sum().to_dict()
                elif aggregation_type == "mean":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    result = df.groupby(group_by)[numeric_cols].mean().to_dict()
                elif aggregation_type == "max":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    result = df.groupby(group_by)[numeric_cols].max().to_dict()
                elif aggregation_type == "min":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    result = df.groupby(group_by)[numeric_cols].min().to_dict()
                else:
                    return {"success": False, "error": "Unsupported aggregation type"}
            else:
                # Overall aggregation
                if aggregation_type == "count":
                    result = len(df)
                elif aggregation_type == "sum":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    result = df[numeric_cols].sum().to_dict()
                elif aggregation_type == "mean":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    result = df[numeric_cols].mean().to_dict()
                else:
                    return {"success": False, "error": "Unsupported aggregation type"}
            
            return {
                "success": True,
                "aggregation_type": aggregation_type,
                "group_by": group_by,
                "results": result
            }
            
        except Exception as e:
            logger.error(f"Data aggregation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_trend_metrics(self, time_series_data: List[Dict], date_column: str, value_column: str) -> Dict[str, Any]:
        """Calculate trend metrics from time series data"""
        try:
            df = pd.DataFrame(time_series_data)
            df[date_column] = pd.to_datetime(df[date_column])
            df = df.sort_values(date_column)
            
            # Calculate basic trend metrics
            values = df[value_column].values
            dates = df[date_column].values
            
            # Linear trend
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)
            
            # Growth rate
            if len(values) > 1:
                growth_rate = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            else:
                growth_rate = 0
            
            # Moving average
            window_size = min(7, len(values))
            moving_avg = df[value_column].rolling(window=window_size).mean().tolist()
            
            # Volatility
            volatility = np.std(values) if len(values) > 1 else 0
            
            # Seasonality detection (simple)
            if len(values) >= 12:  # At least 12 data points for basic seasonality
                seasonal_pattern = self._detect_seasonality(values)
            else:
                seasonal_pattern = "Insufficient data for seasonality analysis"
            
            trend_metrics = {
                "slope": float(slope),
                "intercept": float(intercept),
                "growth_rate_percent": float(growth_rate),
                "volatility": float(volatility),
                "moving_average": moving_avg,
                "seasonal_pattern": seasonal_pattern,
                "trend_direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "data_points": len(values),
                "date_range": {
                    "start": dates[0].isoformat() if len(dates) > 0 else None,
                    "end": dates[-1].isoformat() if len(dates) > 0 else None
                }
            }
            
            return {"success": True, "trend_metrics": trend_metrics}
            
        except Exception as e:
            logger.error(f"Trend calculation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _detect_seasonality(self, values: np.ndarray) -> str:
        """Simple seasonality detection"""
        try:
            if len(values) < 12:
                return "Insufficient data"
            
            # Simple autocorrelation for seasonality
            autocorr = np.correlate(values, values, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Look for peaks in autocorrelation
            peaks = []
            for i in range(1, len(autocorr)-1):
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                    peaks.append(i)
            
            if len(peaks) > 0:
                avg_period = np.mean(peaks)
                if 3 <= avg_period <= 5:
                    return "Weekly seasonality detected"
                elif 10 <= avg_period <= 15:
                    return "Bi-weekly seasonality detected"
                elif 25 <= avg_period <= 35:
                    return "Monthly seasonality detected"
                else:
                    return f"Seasonality detected with {avg_period:.1f} period"
            else:
                return "No clear seasonality pattern"
                
        except Exception:
            return "Seasonality analysis failed"
    
    def normalize_data(self, data: List[Dict], columns: List[str], method: str = "min_max") -> Dict[str, Any]:
        """Normalize data using specified method"""
        try:
            df = pd.DataFrame(data)
            
            normalized_data = df.copy()
            
            for column in columns:
                if column in df.columns and df[column].dtype in ['int64', 'float64']:
                    if method == "min_max":
                        min_val = df[column].min()
                        max_val = df[column].max()
                        if max_val != min_val:
                            normalized_data[column] = (df[column] - min_val) / (max_val - min_val)
                    elif method == "z_score":
                        mean_val = df[column].mean()
                        std_val = df[column].std()
                        if std_val != 0:
                            normalized_data[column] = (df[column] - mean_val) / std_val
                    elif method == "decimal":
                        max_abs = df[column].abs().max()
                        if max_abs != 0:
                            normalized_data[column] = df[column] / max_abs
                    else:
                        return {"success": False, "error": "Unsupported normalization method"}
            
            return {
                "success": True,
                "normalization_method": method,
                "normalized_columns": columns,
                "normalized_data": normalized_data.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Data normalization failed: {e}")
            return {"success": False, "error": str(e)}
    
    def export_data(self, data: List[Dict], format: str, filename: str = None) -> Dict[str, Any]:
        """Export data in specified format"""
        try:
            if format not in self.supported_formats:
                return {"success": False, "error": f"Unsupported format: {format}"}
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"research_data_{timestamp}.{format}"
            
            df = pd.DataFrame(data)
            
            if format == "csv":
                df.to_csv(filename, index=False)
            elif format == "xlsx":
                df.to_excel(filename, index=False)
            elif format == "json":
                df.to_json(filename, orient='records', indent=2)
            elif format == "xml":
                df.to_xml(filename, index=False)
            
            return {
                "success": True,
                "filename": filename,
                "format": format,
                "record_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_data_quality(self, data: List[Dict]) -> Dict[str, Any]:
        """Validate data quality and provide quality metrics"""
        try:
            df = pd.DataFrame(data)
            
            quality_metrics = {
                "total_records": len(df),
                "total_columns": len(df.columns),
                "missing_values": df.isnull().sum().to_dict(),
                "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
                "duplicate_records": df.duplicated().sum(),
                "data_types": df.dtypes.to_dict(),
                "unique_values": {col: df[col].nunique() for col in df.columns},
                "value_ranges": {}
            }
            
            # Calculate value ranges for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                quality_metrics["value_ranges"][col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std())
                }
            
            # Overall quality score
            missing_percentage = np.mean(list(quality_metrics["missing_percentage"].values()))
            duplicate_percentage = quality_metrics["duplicate_records"] / quality_metrics["total_records"]
            quality_score = max(0, 100 - (missing_percentage + duplicate_percentage * 100))
            
            quality_metrics["overall_quality_score"] = float(quality_score)
            quality_metrics["quality_assessment"] = self._assess_quality(quality_score)
            
            return {"success": True, "quality_metrics": quality_metrics}
            
        except Exception as e:
            logger.error(f"Data quality validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _assess_quality(self, quality_score: float) -> str:
        """Assess data quality based on score"""
        if quality_score >= 90:
            return "Excellent"
        elif quality_score >= 80:
            return "Good"
        elif quality_score >= 70:
            return "Fair"
        elif quality_score >= 60:
            return "Poor"
        else:
            return "Very Poor"
