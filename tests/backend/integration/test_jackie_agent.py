"""
Integration tests for Jackie Agent API endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.agents.jackie.app.main import app

@pytest.mark.integration
@pytest.mark.database
class TestJackieAgent:
    """Integration tests for Jackie Agent"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/jackie/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "jackie" in data["agent"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_code_generation(self, async_client: AsyncClient, mock_user_data):
        """Test code generation functionality."""
        request_data = {
            "prompt": "Create a REST API endpoint for user authentication",
            "language": "python",
            "framework": "fastapi",
            "requirements": ["jwt", "password_hashing"]
        }
        
        with patch('backend.agents.jackie.app.services.code_generation_service.CodeGenerationService.generate_code') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "generated_code": """
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt
from passlib.context import CryptContext

app = FastAPI()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/auth/login")
async def login(username: str, password: str):
    # Authentication logic here
    pass
                """,
                "explanation": "This code creates a FastAPI endpoint for user authentication with JWT and password hashing.",
                "language": "python",
                "framework": "fastapi"
            }
            
            response = await async_client.post(
                "/jackie/code/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "generated_code" in data

    @pytest_asyncio.mark.asyncio
    async def test_code_review(self, async_client: AsyncClient, mock_user_data):
        """Test code review functionality."""
        request_data = {
            "code": """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
            """,
            "language": "python",
            "review_type": "security_and_performance"
        }
        
        with patch('backend.agents.jackie.app.services.code_review_service.CodeReviewService.review_code') as mock_review:
            mock_review.return_value = {
                "success": True,
                "review_results": {
                    "overall_score": 8.5,
                    "issues": [
                        {
                            "type": "performance",
                            "severity": "medium",
                            "description": "Consider using sum() function for better performance",
                            "line": 3,
                            "suggestion": "total = sum(item.price for item in items)"
                        }
                    ],
                    "suggestions": [
                        "Add input validation",
                        "Consider error handling for empty items list"
                    ]
                }
            }
            
            response = await async_client.post(
                "/jackie/code/review",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "review_results" in data

    @pytest_asyncio.mark.asyncio
    async def test_debugging_assistance(self, async_client: AsyncClient, mock_user_data):
        """Test debugging assistance functionality."""
        request_data = {
            "error_message": "AttributeError: 'NoneType' object has no attribute 'get'",
            "code_snippet": """
def process_data(data):
    return data.get('value', 0)
            """,
            "language": "python",
            "context": "API endpoint processing"
        }
        
        with patch('backend.agents.jackie.app.services.debugging_service.DebuggingService.debug_issue') as mock_debug:
            mock_debug.return_value = {
                "success": True,
                "debug_analysis": {
                    "root_cause": "data parameter is None",
                    "solution": "Add null check before accessing data",
                    "fixed_code": """
def process_data(data):
    if data is None:
        return 0
    return data.get('value', 0)
                    """,
                    "prevention_tips": [
                        "Always validate input parameters",
                        "Use type hints for better code clarity"
                    ]
                }
            }
            
            response = await async_client.post(
                "/jackie/debug/analyze",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "debug_analysis" in data

    @pytest_asyncio.mark.asyncio
    async def test_architecture_design(self, async_client: AsyncClient, mock_user_data):
        """Test architecture design functionality."""
        request_data = {
            "requirements": "Build a microservices architecture for an e-commerce platform",
            "constraints": ["scalability", "high_availability", "cost_optimization"],
            "tech_stack": ["python", "postgresql", "redis", "docker"]
        }
        
        with patch('backend.agents.jackie.app.services.architecture_service.ArchitectureService.design_architecture') as mock_design:
            mock_design.return_value = {
                "success": True,
                "architecture": {
                    "overview": "Microservices architecture with API Gateway pattern",
                    "services": [
                        {
                            "name": "user-service",
                            "responsibility": "User management and authentication",
                            "tech_stack": ["FastAPI", "PostgreSQL", "Redis"]
                        },
                        {
                            "name": "product-service",
                            "responsibility": "Product catalog and inventory",
                            "tech_stack": ["FastAPI", "PostgreSQL"]
                        }
                    ],
                    "infrastructure": {
                        "api_gateway": "Kong or AWS API Gateway",
                        "service_mesh": "Istio",
                        "monitoring": "Prometheus + Grafana"
                    }
                }
            }
            
            response = await async_client.post(
                "/jackie/architecture/design",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "architecture" in data

    @pytest_asyncio.mark.asyncio
    async def test_database_design(self, async_client: AsyncClient, mock_user_data):
        """Test database design functionality."""
        request_data = {
            "requirements": "Design database for a social media platform",
            "entities": ["users", "posts", "comments", "likes"],
            "relationships": "Users can create posts, comment on posts, and like posts",
            "scale_requirements": "1M+ users, 10M+ posts"
        }
        
        with patch('backend.agents.jackie.app.services.database_design_service.DatabaseDesignService.design_schema') as mock_design:
            mock_design.return_value = {
                "success": True,
                "database_design": {
                    "schema": {
                        "users": {
                            "id": "UUID PRIMARY KEY",
                            "username": "VARCHAR(50) UNIQUE",
                            "email": "VARCHAR(100) UNIQUE",
                            "created_at": "TIMESTAMP"
                        },
                        "posts": {
                            "id": "UUID PRIMARY KEY",
                            "user_id": "UUID REFERENCES users(id)",
                            "content": "TEXT",
                            "created_at": "TIMESTAMP"
                        }
                    },
                    "indexes": [
                        "CREATE INDEX idx_posts_user_id ON posts(user_id)",
                        "CREATE INDEX idx_posts_created_at ON posts(created_at)"
                    ],
                    "optimization_tips": [
                        "Use partitioning for posts table by date",
                        "Consider read replicas for read-heavy queries"
                    ]
                }
            }
            
            response = await async_client.post(
                "/jackie/database/design",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "database_design" in data

    @pytest_asyncio.mark.asyncio
    async def test_api_documentation_generation(self, async_client: AsyncClient, mock_user_data):
        """Test API documentation generation."""
        request_data = {
            "api_spec": {
                "endpoints": [
                    {
                        "path": "/api/users",
                        "method": "GET",
                        "description": "Get all users",
                        "parameters": ["page", "limit"],
                        "response": "List of users"
                    }
                ]
            },
            "format": "openapi",
            "style": "comprehensive"
        }
        
        with patch('backend.agents.jackie.app.services.documentation_service.DocumentationService.generate_api_docs') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "documentation": {
                    "openapi_spec": {
                        "openapi": "3.0.0",
                        "info": {
                            "title": "User API",
                            "version": "1.0.0"
                        },
                        "paths": {
                            "/api/users": {
                                "get": {
                                    "summary": "Get all users",
                                    "parameters": [
                                        {
                                            "name": "page",
                                            "in": "query",
                                            "type": "integer"
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
            
            response = await async_client.post(
                "/jackie/documentation/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "documentation" in data

    @pytest_asyncio.mark.asyncio
    async def test_testing_strategy(self, async_client: AsyncClient, mock_user_data):
        """Test testing strategy generation."""
        request_data = {
            "project_type": "web_application",
            "tech_stack": ["python", "fastapi", "postgresql", "react"],
            "testing_goals": ["unit_tests", "integration_tests", "e2e_tests"],
            "coverage_target": 90
        }
        
        with patch('backend.agents.jackie.app.services.testing_service.TestingService.create_strategy') as mock_create:
            mock_create.return_value = {
                "success": True,
                "testing_strategy": {
                    "unit_tests": {
                        "framework": "pytest",
                        "coverage_target": 90,
                        "focus_areas": ["business_logic", "data_validation"]
                    },
                    "integration_tests": {
                        "framework": "pytest + httpx",
                        "test_database": "test_postgres",
                        "focus_areas": ["api_endpoints", "database_operations"]
                    },
                    "e2e_tests": {
                        "framework": "playwright",
                        "browsers": ["chrome", "firefox"],
                        "focus_areas": ["user_workflows", "critical_paths"]
                    }
                }
            }
            
            response = await async_client.post(
                "/jackie/testing/strategy",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "testing_strategy" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        request_data = {
            "prompt": "Create a simple function",
            "language": "python"
        }
        
        response = await async_client.post(
            "/jackie/code/generate",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_invalid_request_data(self, async_client: AsyncClient):
        """Test handling of invalid request data."""
        request_data = {
            "prompt": "",  # Empty prompt
            "language": "invalid_language"
        }
        
        response = await async_client.post(
            "/jackie/code/generate",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_service_unavailable(self, async_client: AsyncClient):
        """Test handling when services are unavailable."""
        request_data = {
            "prompt": "Create a simple function",
            "language": "python"
        }
        
        with patch('backend.agents.jackie.app.services.code_generation_service.CodeGenerationService.generate_code') as mock_generate:
            mock_generate.side_effect = Exception("Service unavailable")
            
            response = await async_client.post(
                "/jackie/code/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data
