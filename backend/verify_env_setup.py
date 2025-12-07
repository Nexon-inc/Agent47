#!/usr/bin/env python3
"""
Environment Setup Verification Script

This script verifies that all required environment variables are properly set
and that the system can access all necessary API keys and configurations.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from core.config import settings
from core.database.connection import get_supabase
from core.cache.redis_manager import get_redis_manager
from core.event_bus.kafka_manager import get_kafka_manager
from core.storage.chroma_manager import get_chroma_manager
from core.ai import get_ai_service_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentVerifier:
    """Verifies environment setup and API key configuration"""
    
    def __init__(self):
        self.results = {
            "environment_variables": {},
            "database_connection": False,
            "redis_connection": False,
            "kafka_connection": False,
            "chromadb_connection": False,
            "ai_services": {},
            "platform_integrations": {},
            "overall_status": "unknown"
        }
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check if all required environment variables are set"""
        logger.info("🔍 Checking environment variables...")
        
        required_vars = {
            # Core AI Services
            # "CHUTES_API_KEY": "Chutes AI API key for LLM services",  # Removed
            "OPENAI_API_KEY": "OpenAI API key for AI services",
            
            # Database (Supabase)
            "SUPABASE_URL": "Supabase project URL",
            "SUPABASE_ANON_KEY": "Supabase anonymous key",
            "SUPABASE_SERVICE_ROLE_KEY": "Supabase service role key",
            "SUPABASE_DB_URL": "Supabase database connection URL",
            
            # Security
            "JWT_SECRET_KEY": "JWT secret key for authentication",
        }
        
        optional_vars = {
            # Social Media APIs
            "FACEBOOK_APP_ID": "Facebook app ID for social media integration",
            "FACEBOOK_APP_SECRET": "Facebook app secret",
            "TWITTER_API_KEY": "Twitter API key",
            "LINKEDIN_CLIENT_ID": "LinkedIn client ID",
            "TIKTOK_ACCESS_TOKEN": "TikTok access token",
            "PINTEREST_ACCESS_TOKEN": "Pinterest access token",
            "SNAPCHAT_CLIENT_ID": "Snapchat client ID",
            
            # CRM APIs
            "SALESFORCE_CLIENT_ID": "Salesforce client ID",
            "HUBSPOT_API_KEY": "HubSpot API key",
            "PIPEDRIVE_API_KEY": "Pipedrive API key",
            
            # Marketing APIs
            "GOOGLE_ADS_CLIENT_ID": "Google Ads client ID",
            "MAILCHIMP_API_KEY": "Mailchimp API key",
            "SENDGRID_API_KEY": "SendGrid API key",
            
            # Analytics
            "GOOGLE_ANALYTICS_ID": "Google Analytics ID",
            "MIXPANEL_PROJECT_TOKEN": "Mixpanel project token",
            
            # Communication
            "TWILIO_ACCOUNT_SID": "Twilio account SID",
            "SLACK_BOT_TOKEN": "Slack bot token",
            "DISCORD_BOT_TOKEN": "Discord bot token",
        }
        
        env_status = {
            "required": {},
            "optional": {},
            "missing_required": [],
            "missing_optional": [],
            "total_required": len(required_vars),
            "total_optional": len(optional_vars),
            "required_set": 0,
            "optional_set": 0
        }
        
        # Check required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                env_status["required"][var] = {
                    "set": True,
                    "description": description,
                    "value_length": len(value),
                    "value_preview": value[:8] + "..." if len(value) > 8 else value
                }
                env_status["required_set"] += 1
            else:
                env_status["required"][var] = {
                    "set": False,
                    "description": description
                }
                env_status["missing_required"].append(var)
        
        # Check optional variables
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                env_status["optional"][var] = {
                    "set": True,
                    "description": description,
                    "value_length": len(value),
                    "value_preview": value[:8] + "..." if len(value) > 8 else value
                }
                env_status["optional_set"] += 1
            else:
                env_status["optional"][var] = {
                    "set": False,
                    "description": description
                }
                env_status["missing_optional"].append(var)
        
        self.results["environment_variables"] = env_status
        return env_status
    
    async def check_database_connection(self) -> bool:
        """Check database connection"""
        logger.info("🗄️ Checking database connection...")
        try:
            db = await get_supabase()
            async with db.get_session() as session:
                # Simple query to test connection
                result = await session.execute("SELECT 1")
                result.fetchone()
            
            logger.info("✅ Database connection successful")
            self.results["database_connection"] = True
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.results["database_connection"] = False
            return False
    
    async def check_redis_connection(self) -> bool:
        """Check Redis connection"""
        logger.info("🔴 Checking Redis connection...")
        try:
            redis_manager = await get_redis_manager()
            await redis_manager.ping()
            logger.info("✅ Redis connection successful")
            self.results["redis_connection"] = True
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.results["redis_connection"] = False
            return False
    
    async def check_kafka_connection(self) -> bool:
        """Check Kafka connection"""
        logger.info("📨 Checking Kafka connection...")
        try:
            kafka_manager = await get_kafka_manager()
            await kafka_manager.health_check()
            logger.info("✅ Kafka connection successful")
            self.results["kafka_connection"] = True
            return True
        except Exception as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            self.results["kafka_connection"] = False
            return False
    
    async def check_chromadb_connection(self) -> bool:
        """Check ChromaDB connection"""
        logger.info("🧠 Checking ChromaDB connection...")
        try:
            chroma_manager = await get_chroma_manager()
            await chroma_manager.health_check()
            logger.info("✅ ChromaDB connection successful")
            self.results["chromadb_connection"] = True
            return True
        except Exception as e:
            logger.error(f"❌ ChromaDB connection failed: {e}")
            self.results["chromadb_connection"] = False
            return False
    
    async def check_ai_services(self) -> Dict[str, Any]:
        """Check AI services configuration"""
        logger.info("🤖 Checking AI services...")
        
        ai_status = {
            # "chutes_ai": {  # Removed
            #     "configured": bool(settings.chutes.chutes_api_key),
            #     "api_url": settings.chutes.chutes_api_url,
            #     "model": settings.chutes.chutes_llm_model
            # },
            "grok_llm": {
                "configured": bool(settings.grok.grok_api_url),
                "api_url": settings.grok.grok_api_url,
                "model_path": settings.grok.grok_model_path
            },
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "api_key_set": bool(os.getenv("OPENAI_API_KEY"))
            }
        }
        
        # Test AI service manager
        try:
            ai_manager = await get_ai_service_manager()
            health_status = await ai_manager.health_check()
            ai_status["service_manager"] = {
                "initialized": True,
                "health_status": health_status
            }
            logger.info("✅ AI service manager initialized successfully")
        except Exception as e:
            ai_status["service_manager"] = {
                "initialized": False,
                "error": str(e)
            }
            logger.error(f"❌ AI service manager initialization failed: {e}")
        
        self.results["ai_services"] = ai_status
        return ai_status
    
    def check_platform_integrations(self) -> Dict[str, Any]:
        """Check platform integration configurations"""
        logger.info("🔗 Checking platform integrations...")
        
        platforms = {
            "facebook": {
                "app_id": bool(settings.facebook.app_id),
                "app_secret": bool(settings.facebook.app_secret)
            },
            "twitter": {
                "api_key": bool(os.getenv("TWITTER_API_KEY")),
                "api_secret": bool(os.getenv("TWITTER_API_SECRET")),
                "access_token": bool(os.getenv("TWITTER_ACCESS_TOKEN"))
            },
            "linkedin": {
                "client_id": bool(settings.linkedin.client_id),
                "client_secret": bool(settings.linkedin.client_secret)
            },
            "slack": {
                "bot_token": bool(settings.slack.bot_token),
                "signing_secret": bool(settings.slack.signing_secret)
            },
            "aws": {
                "access_key": bool(settings.s3.aws_access_key_id),
                "secret_key": bool(settings.s3.aws_secret_access_key),
                "bucket": bool(settings.s3.bucket_name)
            }
        }
        
        self.results["platform_integrations"] = platforms
        return platforms
    
    def generate_report(self) -> str:
        """Generate a comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("🚀 AGENT47 ENVIRONMENT VERIFICATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Environment Variables
        env_vars = self.results["environment_variables"]
        report.append("📋 ENVIRONMENT VARIABLES")
        report.append("-" * 40)
        report.append(f"Required Variables: {env_vars['required_set']}/{env_vars['total_required']} set")
        report.append(f"Optional Variables: {env_vars['optional_set']}/{env_vars['total_optional']} set")
        report.append("")
        
        if env_vars["missing_required"]:
            report.append("❌ MISSING REQUIRED VARIABLES:")
            for var in env_vars["missing_required"]:
                report.append(f"   - {var}: {env_vars['required'][var]['description']}")
            report.append("")
        
        if env_vars["missing_optional"]:
            report.append("⚠️  MISSING OPTIONAL VARIABLES:")
            for var in env_vars["missing_optional"][:10]:  # Show first 10
                report.append(f"   - {var}: {env_vars['optional'][var]['description']}")
            if len(env_vars["missing_optional"]) > 10:
                report.append(f"   ... and {len(env_vars['missing_optional']) - 10} more")
            report.append("")
        
        # Core Services
        report.append("🔧 CORE SERVICES")
        report.append("-" * 40)
        report.append(f"Database: {'✅ Connected' if self.results['database_connection'] else '❌ Failed'}")
        report.append(f"Redis: {'✅ Connected' if self.results['redis_connection'] else '❌ Failed'}")
        report.append(f"Kafka: {'✅ Connected' if self.results['kafka_connection'] else '❌ Failed'}")
        report.append(f"ChromaDB: {'✅ Connected' if self.results['chromadb_connection'] else '❌ Failed'}")
        report.append("")
        
        # AI Services
        ai_services = self.results["ai_services"]
        report.append("🤖 AI SERVICES")
        report.append("-" * 40)
        # report.append(f"Chutes AI: {'✅ Configured' if ai_services['chutes_ai']['configured'] else '❌ Not configured'}")  # Removed
        report.append(f"Grok LLM: {'✅ Configured' if ai_services['grok_llm']['configured'] else '❌ Not configured'}")
        report.append(f"OpenAI: {'✅ Configured' if ai_services['openai']['configured'] else '❌ Not configured'}")
        report.append(f"Service Manager: {'✅ Initialized' if ai_services['service_manager']['initialized'] else '❌ Failed'}")
        report.append("")
        
        # Platform Integrations
        platforms = self.results["platform_integrations"]
        report.append("🔗 PLATFORM INTEGRATIONS")
        report.append("-" * 40)
        for platform, config in platforms.items():
            configured_count = sum(1 for v in config.values() if v)
            total_count = len(config)
            status = "✅" if configured_count == total_count else "⚠️" if configured_count > 0 else "❌"
            report.append(f"{platform.title()}: {status} {configured_count}/{total_count} configured")
        report.append("")
        
        # Overall Status
        required_vars_ok = len(env_vars["missing_required"]) == 0
        core_services_ok = all([
            self.results["database_connection"],
            self.results["redis_connection"],
            self.results["kafka_connection"],
            self.results["chromadb_connection"]
        ])
        ai_services_ok = ai_services["service_manager"]["initialized"]
        
        if required_vars_ok and core_services_ok and ai_services_ok:
            self.results["overall_status"] = "ready"
            report.append("🎉 OVERALL STATUS: ✅ READY TO RUN")
            report.append("")
            report.append("The Agent47 platform is properly configured and ready to start!")
            report.append("Run: docker-compose up -d")
        else:
            self.results["overall_status"] = "issues"
            report.append("⚠️  OVERALL STATUS: ❌ CONFIGURATION ISSUES")
            report.append("")
            report.append("Please fix the issues above before starting the platform.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    async def run_verification(self) -> Dict[str, Any]:
        """Run complete environment verification"""
        logger.info("🚀 Starting Agent47 environment verification...")
        
        # Check environment variables
        self.check_environment_variables()
        
        # Check core services
        await self.check_database_connection()
        await self.check_redis_connection()
        await self.check_kafka_connection()
        await self.check_chromadb_connection()
        
        # Check AI services
        await self.check_ai_services()
        
        # Check platform integrations
        self.check_platform_integrations()
        
        # Generate and display report
        report = self.generate_report()
        print(report)
        
        return self.results

async def main():
    """Main verification function"""
    verifier = EnvironmentVerifier()
    results = await verifier.run_verification()
    
    # Exit with appropriate code
    if results["overall_status"] == "ready":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
