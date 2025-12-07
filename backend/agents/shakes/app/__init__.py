# Shakes - AI-Powered Content Creation Agent
# This package contains the main application for Shakes, an intelligent content creation system

"""
Shakes - AI-Powered Content Creation Agent

Shakes is an intelligent, AI-driven content creation system that produces high-quality,
platform-specific content quickly, optimizes it for SEO, and enables repurposing across
multiple channels.

Key Features:
- Blog & Article Writing with AI-powered research
- Social Media Content for all major platforms
- SEO Optimization and keyword integration
- Video & Podcast Scripting
- Ad Copywriting for multiple platforms
- Email & Newsletter Writing
- Website & Landing Page Content
- Content Repurposing and transformation
- AI-Powered Content Generation
- Social Media Content Automation
- Grammar & Tone Refinement
- Plagiarism Detection
- Brand Voice Customization
- Multi-Language Content Creation
- Content Collaboration Tools
- Performance Analytics and A/B testing
- And many more advanced features...

Architecture:
- FastAPI-based REST API
- PostgreSQL database with SQLAlchemy ORM
- Redis for caching and session management
- Kafka for event-driven messaging
- Grok LLM for advanced content generation
- ChromaDB for vector search and semantic matching
- AWS S3 for file storage
- Comprehensive analytics and reporting

Modules:
- models: Database models and schemas
- services: Business logic and service layer
- routers: API endpoints and route handlers
- core: Core utilities and configurations
- schemas: Pydantic models for request/response validation
"""

__version__ = "1.0.0"
__author__ = "Agent47 Team"
__description__ = "AI-Powered Content Creation Agent"

# Import main application components
from .main import app, build_app
from .models import *
from .core import *

# Export main components
__all__ = [
    "app",
    "build_app",
    "__version__",
    "__author__",
    "__description__"
]
