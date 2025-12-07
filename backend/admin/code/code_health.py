import asyncio
import ast
import subprocess
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class HealthStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"

class CodeMetric(Enum):
    COMPLEXITY = "complexity"
    COVERAGE = "coverage"
    DUPLICATION = "duplication"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class CodeHealthReport:
    report_id: str
    project_path: str
    overall_health: HealthStatus
    health_score: float
    metrics: Dict[CodeMetric, float]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime
    analysis_duration_seconds: float

@dataclass
class CodeIssue:
    issue_id: str
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    message: str
    rule_id: str
    fix_suggestion: Optional[str]

class CodeHealth(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.analysis_tools = {
            "pylint": self._run_pylint,
            "flake8": self._run_flake8,
            "bandit": self._run_bandit,
            "mypy": self._run_mypy,
            "coverage": self._run_coverage
        }
        self.health_thresholds = {
            HealthStatus.EXCELLENT: 90.0,
            HealthStatus.GOOD: 75.0,
            HealthStatus.WARNING: 60.0,
            HealthStatus.CRITICAL: 40.0
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing CodeHealth...")
            self.database = get_database()
            await self._setup_health_tables()
            self.logger.info("CodeHealth initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize CodeHealth: {str(e)}")
            return False

    async def _setup_health_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS code_health_reports (
                    id SERIAL PRIMARY KEY,
                    report_id VARCHAR(255) UNIQUE NOT NULL,
                    project_path VARCHAR(500) NOT NULL,
                    overall_health VARCHAR(20) NOT NULL,
                    health_score FLOAT NOT NULL,
                    metrics JSONB NOT NULL,
                    issues JSONB NOT NULL,
                    recommendations JSONB NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analysis_duration_seconds FLOAT NOT NULL
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS code_issues (
                    id SERIAL PRIMARY KEY,
                    issue_id VARCHAR(255) UNIQUE NOT NULL,
                    report_id VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    line_number INTEGER NOT NULL,
                    issue_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    rule_id VARCHAR(100),
                    fix_suggestion TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES code_health_reports(report_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_code_health_reports_project 
                ON code_health_reports(project_path);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_code_health_reports_generated_at 
                ON code_health_reports(generated_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_code_issues_report_id 
                ON code_issues(report_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_code_issues_severity 
                ON code_issues(severity);
            """)
            
            await session.commit()

    async def analyze_code_health(
        self,
        project_path: str,
        include_tests: bool = True,
        tools: Optional[List[str]] = None
    ) -> CodeHealthReport:
        start_time = datetime.utcnow()
        
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if tools is None:
            tools = list(self.analysis_tools.keys())
        
        report_id = f"health_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(project_path) % 10000}"
        
        try:
            metrics = {}
            all_issues = []
            
            for tool in tools:
                if tool in self.analysis_tools:
                    try:
                        tool_metrics, tool_issues = await self.analysis_tools[tool](project_path, include_tests)
                        metrics.update(tool_metrics)
                        all_issues.extend(tool_issues)
                    except Exception as e:
                        self.logger.warning(f"Tool {tool} failed: {str(e)}")
            
            health_score = self._calculate_health_score(metrics, all_issues)
            overall_health = self._determine_health_status(health_score)
            recommendations = self._generate_recommendations(metrics, all_issues)
            
            analysis_duration = (datetime.utcnow() - start_time).total_seconds()
            
            report = CodeHealthReport(
                report_id=report_id,
                project_path=project_path,
                overall_health=overall_health,
                health_score=health_score,
                metrics=metrics,
                issues=all_issues,
                recommendations=recommendations,
                generated_at=start_time,
                analysis_duration_seconds=analysis_duration
            )
            
            await self._save_health_report(report)
            return report
            
        except Exception as e:
            self.logger.error(f"Code health analysis failed: {str(e)}")
            raise

    def _calculate_health_score(self, metrics: Dict[CodeMetric, float], issues: List[Dict[str, Any]]) -> float:
        base_score = 100.0
        
        for metric, value in metrics.items():
            if metric == CodeMetric.COMPLEXITY:
                if value > 10:
                    base_score -= min((value - 10) * 2, 20)
            elif metric == CodeMetric.COVERAGE:
                if value < 80:
                    base_score -= (80 - value) * 0.5
            elif metric == CodeMetric.DUPLICATION:
                base_score -= min(value * 5, 15)
            elif metric == CodeMetric.MAINTAINABILITY:
                if value < 70:
                    base_score -= (70 - value) * 0.3
            elif metric == CodeMetric.SECURITY:
                if value < 90:
                    base_score -= (90 - value) * 0.8
            elif metric == CodeMetric.PERFORMANCE:
                if value < 80:
                    base_score -= (80 - value) * 0.4
        
        for issue in issues:
            severity = issue.get("severity", "info")
            if severity == "error":
                base_score -= 2
            elif severity == "warning":
                base_score -= 1
            elif severity == "info":
                base_score -= 0.5
        
        return max(0.0, min(100.0, base_score))

    def _determine_health_status(self, health_score: float) -> HealthStatus:
        if health_score >= self.health_thresholds[HealthStatus.EXCELLENT]:
            return HealthStatus.EXCELLENT
        elif health_score >= self.health_thresholds[HealthStatus.GOOD]:
            return HealthStatus.GOOD
        elif health_score >= self.health_thresholds[HealthStatus.WARNING]:
            return HealthStatus.WARNING
        elif health_score >= self.health_thresholds[HealthStatus.CRITICAL]:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.FAILED

    def _generate_recommendations(self, metrics: Dict[CodeMetric, float], issues: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        
        if CodeMetric.COVERAGE in metrics and metrics[CodeMetric.COVERAGE] < 80:
            recommendations.append("Increase test coverage to at least 80%")
        
        if CodeMetric.COMPLEXITY in metrics and metrics[CodeMetric.COMPLEXITY] > 10:
            recommendations.append("Reduce code complexity by breaking down large functions")
        
        if CodeMetric.DUPLICATION in metrics and metrics[CodeMetric.DUPLICATION] > 3:
            recommendations.append("Reduce code duplication by extracting common functionality")
        
        if CodeMetric.SECURITY in metrics and metrics[CodeMetric.SECURITY] < 90:
            recommendations.append("Address security vulnerabilities and implement security best practices")
        
        error_issues = [issue for issue in issues if issue.get("severity") == "error"]
        if len(error_issues) > 0:
            recommendations.append(f"Fix {len(error_issues)} critical errors")
        
        warning_issues = [issue for issue in issues if issue.get("severity") == "warning"]
        if len(warning_issues) > 10:
            recommendations.append(f"Address {len(warning_issues)} warnings to improve code quality")
        
        return recommendations

    async def _run_pylint(self, project_path: str, include_tests: bool) -> Tuple[Dict[CodeMetric, float], List[Dict[str, Any]]]:
        try:
            cmd = ["pylint", "--output-format=json", project_path]
            if not include_tests:
                cmd.extend(["--ignore=tests", "--ignore=test_*.py"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            metrics = {}
            issues = []
            
            if result.stdout:
                try:
                    pylint_data = json.loads(result.stdout)
                    for item in pylint_data:
                        if item.get("type") == "convention":
                            continue
                        
                        issue = {
                            "file_path": item.get("path", ""),
                            "line_number": item.get("line", 0),
                            "issue_type": "pylint",
                            "severity": "error" if item.get("type") == "error" else "warning",
                            "message": item.get("message", ""),
                            "rule_id": item.get("message-id", ""),
                            "fix_suggestion": None
                        }
                        issues.append(issue)
                    
                    if pylint_data:
                        total_score = sum(item.get("score", 0) for item in pylint_data if "score" in item)
                        avg_score = total_score / len(pylint_data) if pylint_data else 0
                        metrics[CodeMetric.MAINTAINABILITY] = max(0, avg_score)
                
                except json.JSONDecodeError:
                    pass
            
            return metrics, issues
            
        except subprocess.TimeoutExpired:
            self.logger.warning("Pylint analysis timed out")
            return {}, []
        except Exception as e:
            self.logger.error(f"Pylint analysis failed: {str(e)}")
            return {}, []

    async def _run_flake8(self, project_path: str, include_tests: bool) -> Tuple[Dict[CodeMetric, float], List[Dict[str, Any]]]:
        try:
            cmd = ["flake8", "--format=%(path)s:%(row)d:%(col)d:%(code)s:%(text)s", project_path]
            if not include_tests:
                cmd.extend(["--exclude=tests,test_*.py"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            issues = []
            error_count = 0
            warning_count = 0
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(':', 4)
                if len(parts) >= 5:
                    file_path, line_num, col_num, code, message = parts
                    
                    severity = "error" if code.startswith('E') else "warning"
                    if severity == "error":
                        error_count += 1
                    else:
                        warning_count += 1
                    
                    issue = {
                        "file_path": file_path,
                        "line_number": int(line_num),
                        "issue_type": "flake8",
                        "severity": severity,
                        "message": message.strip(),
                        "rule_id": code,
                        "fix_suggestion": None
                    }
                    issues.append(issue)
            
            metrics = {}
            if error_count + warning_count > 0:
                quality_score = max(0, 100 - (error_count * 5 + warning_count * 2))
                metrics[CodeMetric.MAINTAINABILITY] = quality_score
            
            return metrics, issues
            
        except subprocess.TimeoutExpired:
            self.logger.warning("Flake8 analysis timed out")
            return {}, []
        except Exception as e:
            self.logger.error(f"Flake8 analysis failed: {str(e)}")
            return {}, []

    async def _run_bandit(self, project_path: str, include_tests: bool) -> Tuple[Dict[CodeMetric, float], List[Dict[str, Any]]]:
        try:
            cmd = ["bandit", "-r", "-f", "json", project_path]
            if not include_tests:
                cmd.extend(["-x", "tests"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            metrics = {}
            issues = []
            
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    
                    for item in bandit_data.get("results", []):
                        severity_map = {"HIGH": "error", "MEDIUM": "warning", "LOW": "info"}
                        severity = severity_map.get(item.get("issue_severity", "LOW"), "info")
                        
                        issue = {
                            "file_path": item.get("filename", ""),
                            "line_number": item.get("line_number", 0),
                            "issue_type": "security",
                            "severity": severity,
                            "message": item.get("issue_text", ""),
                            "rule_id": item.get("test_id", ""),
                            "fix_suggestion": item.get("issue_confidence", "")
                        }
                        issues.append(issue)
                    
                    high_severity = len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "HIGH"])
                    medium_severity = len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "MEDIUM"])
                    
                    security_score = max(0, 100 - (high_severity * 20 + medium_severity * 10))
                    metrics[CodeMetric.SECURITY] = security_score
                
                except json.JSONDecodeError:
                    pass
            
            return metrics, issues
            
        except subprocess.TimeoutExpired:
            self.logger.warning("Bandit analysis timed out")
            return {}, []
        except Exception as e:
            self.logger.error(f"Bandit analysis failed: {str(e)}")
            return {}, []

    async def _run_mypy(self, project_path: str, include_tests: bool) -> Tuple[Dict[CodeMetric, float], List[Dict[str, Any]]]:
        try:
            cmd = ["mypy", "--show-error-codes", "--no-error-summary", project_path]
            if not include_tests:
                cmd.extend(["--exclude", "tests/"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            issues = []
            error_count = 0
            
            for line in result.stdout.strip().split('\n'):
                if not line or ':' not in line:
                    continue
                
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    file_path, line_num, col_num, message = parts
                    
                    error_count += 1
                    
                    issue = {
                        "file_path": file_path,
                        "line_number": int(line_num),
                        "issue_type": "type_check",
                        "severity": "error",
                        "message": message.strip(),
                        "rule_id": "mypy",
                        "fix_suggestion": "Add type annotations"
                    }
                    issues.append(issue)
            
            metrics = {}
            if error_count > 0:
                type_safety_score = max(0, 100 - (error_count * 3))
                metrics[CodeMetric.MAINTAINABILITY] = type_safety_score
            
            return metrics, issues
            
        except subprocess.TimeoutExpired:
            self.logger.warning("MyPy analysis timed out")
            return {}, []
        except Exception as e:
            self.logger.error(f"MyPy analysis failed: {str(e)}")
            return {}, []

    async def _run_coverage(self, project_path: str, include_tests: bool) -> Tuple[Dict[CodeMetric, float], List[Dict[str, Any]]]:
        try:
            if not include_tests:
                return {}, []
            
            cmd = ["coverage", "run", "-m", "pytest", "--tb=short"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=project_path)
            
            if result.returncode != 0:
                self.logger.warning("Test execution failed for coverage analysis")
                return {}, []
            
            report_cmd = ["coverage", "report", "--format=json"]
            report_result = subprocess.run(report_cmd, capture_output=True, text=True, timeout=60, cwd=project_path)
            
            metrics = {}
            
            if report_result.stdout:
                try:
                    coverage_data = json.loads(report_result.stdout)
                    total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                    metrics[CodeMetric.COVERAGE] = float(total_coverage)
                except json.JSONDecodeError:
                    pass
            
            return metrics, []
            
        except subprocess.TimeoutExpired:
            self.logger.warning("Coverage analysis timed out")
            return {}, []
        except Exception as e:
            self.logger.error(f"Coverage analysis failed: {str(e)}")
            return {}, []

    async def _save_health_report(self, report: CodeHealthReport):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO code_health_reports (
                        report_id, project_path, overall_health, health_score, metrics,
                        issues, recommendations, analysis_duration_seconds
                    ) VALUES (
                        :report_id, :project_path, :overall_health, :health_score, :metrics,
                        :issues, :recommendations, :analysis_duration_seconds
                    )
                """, {
                    "report_id": report.report_id,
                    "project_path": report.project_path,
                    "overall_health": report.overall_health.value,
                    "health_score": report.health_score,
                    "metrics": {k.value: v for k, v in report.metrics.items()},
                    "issues": report.issues,
                    "recommendations": report.recommendations,
                    "analysis_duration_seconds": report.analysis_duration_seconds
                })
                
                for issue in report.issues:
                    issue_id = f"issue_{hash(str(issue)) % 100000}"
                    await session.execute("""
                        INSERT INTO code_issues (
                            issue_id, report_id, file_path, line_number, issue_type,
                            severity, message, rule_id, fix_suggestion
                        ) VALUES (
                            :issue_id, :report_id, :file_path, :line_number, :issue_type,
                            :severity, :message, :rule_id, :fix_suggestion
                        )
                    """, {
                        "issue_id": issue_id,
                        "report_id": report.report_id,
                        "file_path": issue.get("file_path", ""),
                        "line_number": issue.get("line_number", 0),
                        "issue_type": issue.get("issue_type", ""),
                        "severity": issue.get("severity", ""),
                        "message": issue.get("message", ""),
                        "rule_id": issue.get("rule_id", ""),
                        "fix_suggestion": issue.get("fix_suggestion")
                    })
                
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save health report: {str(e)}")

    async def get_health_reports(
        self,
        project_path: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CodeHealthReport]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if project_path:
            conditions.append("project_path = :project_path")
            params["project_path"] = project_path
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT report_id, project_path, overall_health, health_score, metrics,
                       issues, recommendations, generated_at, analysis_duration_seconds
                FROM code_health_reports
                {where_clause}
                ORDER BY generated_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            reports = []
            for row in result:
                report = CodeHealthReport(
                    report_id=row.report_id,
                    project_path=row.project_path,
                    overall_health=HealthStatus(row.overall_health),
                    health_score=row.health_score,
                    metrics={CodeMetric(k): v for k, v in row.metrics.items()},
                    issues=row.issues or [],
                    recommendations=row.recommendations or [],
                    generated_at=row.generated_at,
                    analysis_duration_seconds=row.analysis_duration_seconds
                )
                reports.append(report)
            
            return reports

    async def get_health_trends(
        self,
        project_path: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    DATE(generated_at) as date,
                    AVG(health_score) as avg_health_score,
                    COUNT(*) as report_count,
                    AVG(analysis_duration_seconds) as avg_analysis_duration
                FROM code_health_reports
                WHERE project_path = :project_path
                AND generated_at >= :start_date
                GROUP BY DATE(generated_at)
                ORDER BY date
            """, {"project_path": project_path, "start_date": start_date})
            
            trends = []
            for row in result:
                trend = {
                    "date": row.date.isoformat(),
                    "avg_health_score": float(row.avg_health_score),
                    "report_count": row.report_count,
                    "avg_analysis_duration": float(row.avg_analysis_duration)
                }
                trends.append(trend)
            
            return trends

    async def get_health_summary(self, project_path: str) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    overall_health,
                    AVG(health_score) as avg_health_score,
                    COUNT(*) as total_reports,
                    MAX(generated_at) as last_analysis
                FROM code_health_reports
                WHERE project_path = :project_path
                GROUP BY overall_health
            """, {"project_path": project_path})
            
            summary = {
                "project_path": project_path,
                "health_distribution": {},
                "avg_health_score": 0,
                "total_reports": 0,
                "last_analysis": None
            }
            
            total_score = 0
            total_reports = 0
            latest_analysis = None
            
            for row in result:
                summary["health_distribution"][row.overall_health] = {
                    "count": row.total_reports,
                    "avg_score": float(row.avg_health_score)
                }
                total_score += row.avg_health_score * row.total_reports
                total_reports += row.total_reports
                
                if latest_analysis is None or row.last_analysis > latest_analysis:
                    latest_analysis = row.last_analysis
            
            if total_reports > 0:
                summary["avg_health_score"] = total_score / total_reports
                summary["total_reports"] = total_reports
                summary["last_analysis"] = latest_analysis.isoformat() if latest_analysis else None
            
            return summary

_code_health: Optional[CodeHealth] = None

async def get_code_health() -> CodeHealth:
    global _code_health
    if _code_health is None:
        _code_health = CodeHealth()
        await _code_health.initialize()
    return _code_health

async def init_code_health() -> CodeHealth:
    return await get_code_health()
