"""
Integration tests for Admin Services
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.admin.admin_core import app

@pytest.mark.integration
@pytest.mark.database
class TestAdminServices:
    """Integration tests for Admin Services"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test admin health check endpoint."""
        response = await async_client.get("/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "admin" in data["service"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_user_management(self, async_client: AsyncClient, mock_user_data):
        """Test user management functionality."""
        request_data = {
            "action": "get_users",
            "filters": {
                "subscription_tier": "pro",
                "is_active": True
            },
            "pagination": {
                "page": 1,
                "limit": 10
            }
        }
        
        with patch('backend.admin.users.user_manager.UserManager.get_users') as mock_get_users:
            mock_get_users.return_value = {
                "success": True,
                "users": [
                    {
                        "id": 1,
                        "email": "user1@example.com",
                        "username": "user1",
                        "subscription_tier": "pro",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total_count": 1,
                "page": 1,
                "limit": 10
            }
            
            response = await async_client.post(
                "/admin/users/manage",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "users" in data

    @pytest_asyncio.mark.asyncio
    async def test_agent_monitoring(self, async_client: AsyncClient, mock_user_data):
        """Test agent monitoring functionality."""
        request_data = {
            "monitoring_type": "performance",
            "timeframe": "24_hours",
            "agents": ["aria", "clara", "eric"]
        }
        
        with patch('backend.admin.agents.agent_monitor.AgentMonitor.get_agent_metrics') as mock_get_metrics:
            mock_get_metrics.return_value = {
                "success": True,
                "metrics": {
                    "aria": {
                        "requests_per_hour": 150,
                        "average_response_time": 1.2,
                        "success_rate": 0.98,
                        "error_rate": 0.02
                    },
                    "clara": {
                        "requests_per_hour": 200,
                        "average_response_time": 0.8,
                        "success_rate": 0.99,
                        "error_rate": 0.01
                    },
                    "eric": {
                        "requests_per_hour": 100,
                        "average_response_time": 1.5,
                        "success_rate": 0.95,
                        "error_rate": 0.05
                    }
                }
            }
            
            response = await async_client.post(
                "/admin/agents/monitor",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "metrics" in data

    @pytest_asyncio.mark.asyncio
    async def test_system_analytics(self, async_client: AsyncClient, mock_user_data):
        """Test system analytics functionality."""
        request_data = {
            "analytics_type": "usage_statistics",
            "timeframe": "7_days",
            "metrics": ["active_users", "api_calls", "revenue"]
        }
        
        with patch('backend.admin.analytics.analytics_manager.AnalyticsManager.get_system_analytics') as mock_get_analytics:
            mock_get_analytics.return_value = {
                "success": True,
                "analytics": {
                    "active_users": {
                        "total": 1250,
                        "new_users": 150,
                        "retention_rate": 0.85
                    },
                    "api_calls": {
                        "total_calls": 50000,
                        "successful_calls": 49500,
                        "failed_calls": 500
                    },
                    "revenue": {
                        "total_revenue": 25000,
                        "subscription_revenue": 20000,
                        "usage_revenue": 5000
                    }
                }
            }
            
            response = await async_client.post(
                "/admin/analytics/system",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analytics" in data

    @pytest_asyncio.mark.asyncio
    async def test_financial_reporting(self, async_client: AsyncClient, mock_user_data):
        """Test financial reporting functionality."""
        request_data = {
            "report_type": "revenue_analysis",
            "timeframe": "monthly",
            "period": "2024-01"
        }
        
        with patch('backend.admin.finance.financial_reporting.FinancialReporting.generate_report') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "report": {
                    "revenue_breakdown": {
                        "subscription_revenue": 20000,
                        "usage_revenue": 5000,
                        "one_time_payments": 2000
                    },
                    "expense_breakdown": {
                        "infrastructure_costs": 8000,
                        "ai_service_costs": 3000,
                        "operational_costs": 2000
                    },
                    "profit_margin": 0.65,
                    "growth_rate": 0.15
                }
            }
            
            response = await async_client.post(
                "/admin/finance/reports",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "report" in data

    @pytest_asyncio.mark.asyncio
    async def test_database_management(self, async_client: AsyncClient, mock_user_data):
        """Test database management functionality."""
        request_data = {
            "action": "backup",
            "backup_type": "full",
            "retention_days": 30
        }
        
        with patch('backend.admin.database.backup_manager.BackupManager.create_backup') as mock_backup:
            mock_backup.return_value = {
                "success": True,
                "backup": {
                    "backup_id": "BACKUP-12345",
                    "backup_size": "2.5GB",
                    "backup_location": "s3://backups/backup-12345.sql",
                    "created_at": "2024-01-01T00:00:00Z",
                    "expires_at": "2024-01-31T00:00:00Z"
                }
            }
            
            response = await async_client.post(
                "/admin/database/backup",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "backup" in data

    @pytest_asyncio.mark.asyncio
    async def test_security_monitoring(self, async_client: AsyncClient, mock_user_data):
        """Test security monitoring functionality."""
        request_data = {
            "monitoring_type": "threat_detection",
            "timeframe": "24_hours",
            "alert_level": "high"
        }
        
        with patch('backend.admin.security.threat_detection.ThreatDetection.get_security_alerts') as mock_get_alerts:
            mock_get_alerts.return_value = {
                "success": True,
                "alerts": [
                    {
                        "alert_id": "ALERT-12345",
                        "severity": "high",
                        "type": "suspicious_login",
                        "description": "Multiple failed login attempts from IP 192.168.1.100",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "status": "active"
                    }
                ],
                "summary": {
                    "total_alerts": 1,
                    "high_severity": 1,
                    "medium_severity": 0,
                    "low_severity": 0
                }
            }
            
            response = await async_client.post(
                "/admin/security/alerts",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "alerts" in data

    @pytest_asyncio.mark.asyncio
    async def test_integration_management(self, async_client: AsyncClient, mock_user_data):
        """Test integration management functionality."""
        request_data = {
            "action": "get_integrations",
            "status": "active",
            "integration_type": "ai_services"
        }
        
        with patch('backend.admin.integrations.integration_admin_manager.IntegrationAdminManager.get_integrations') as mock_get_integrations:
            mock_get_integrations.return_value = {
                "success": True,
                "integrations": [
                    {
                        "integration_id": "INT-12345",
                        "name": "Chutes AI",
                        "type": "ai_service",
                        "status": "active",
                        "health_score": 0.95,
                        "last_health_check": "2024-01-01T12:00:00Z"
                    },
                    {
                        "integration_id": "INT-12346",
                        "name": "Grok LLM",
                        "type": "ai_service",
                        "status": "active",
                        "health_score": 0.98,
                        "last_health_check": "2024-01-01T12:00:00Z"
                    }
                ]
            }
            
            response = await async_client.post(
                "/admin/integrations/manage",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "integrations" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to admin endpoints."""
        request_data = {
            "action": "get_users",
            "filters": {}
        }
        
        response = await async_client.post(
            "/admin/users/manage",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_insufficient_permissions(self, async_client: AsyncClient):
        """Test insufficient permissions for admin endpoints."""
        request_data = {
            "action": "get_users",
            "filters": {}
        }
        
        response = await async_client.post(
            "/admin/users/manage",
            json=request_data,
            headers={"Authorization": f"Bearer user_token"}  # Regular user token
        )
        
        assert response.status_code == 403

    @pytest_asyncio.mark.asyncio
    async def test_invalid_request_data(self, async_client: AsyncClient):
        """Test handling of invalid request data."""
        request_data = {
            "action": "",  # Empty action
            "filters": "invalid_filters"  # Invalid filters format
        }
        
        response = await async_client.post(
            "/admin/users/manage",
            json=request_data,
            headers={"Authorization": f"Bearer admin_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_service_unavailable(self, async_client: AsyncClient):
        """Test handling when admin services are unavailable."""
        request_data = {
            "action": "get_users",
            "filters": {}
        }
        
        with patch('backend.admin.users.user_manager.UserManager.get_users') as mock_get_users:
            mock_get_users.side_effect = Exception("Database connection failed")
            
            response = await async_client.post(
                "/admin/users/manage",
                json=request_data,
                headers={"Authorization": f"Bearer admin_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data
