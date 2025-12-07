# Clara - AI-Powered Customer Support Agent
# This package contains the main application for Clara, an intelligent customer support system

"""
Clara - AI-Powered Customer Support Agent

Clara is an intelligent, 24/7 customer support system that provides comprehensive
customer service across multiple channels including chat, email, phone, social media,
and help desk tickets.

Key Features:
- 24/7 Customer Support with AI-powered responses
- Multichannel Support (chat, email, phone, social media, help desk)
- Automated Responses using NLP
- Live Chat Handoff to human agents
- Sentiment Analysis for priority management
- Knowledge Base Integration
- Ticket Management and Automation
- Voice Assistant Integration
- Feedback Collection and Analysis
- Order & Account Support
- AI Chatbot with Human Escalation
- Omnichannel Customer Engagement
- CRM & Helpdesk Integration
- Predictive Analytics
- Self-Service Customer Portal
- Agent Training Tools
- Customer Journey Tracking
- Multi-Brand Support
- And many more advanced features...

Architecture:
- FastAPI-based REST API
- PostgreSQL database with SQLAlchemy ORM
- Redis for caching and session management
- Kafka for event-driven messaging
- OpenAI GPT-4 for advanced language processing
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
__description__ = "AI-Powered Customer Support Agent"

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
