"""
Setup Verification Script
Verifies that all new services and configurations are properly set up
Run this before starting the server to check for any issues
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

async def verify_setup():
    """Verify all new services and configurations"""
    print("🔍 Verifying Agent47 Setup...")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # 1. Check environment variables
    print("\n1. Checking Environment Variables...")
    from core.config import settings
    
    # Check Google Maps
    if not settings.google_maps.google_maps_api_key:
        warnings.append("⚠️  GOOGLE_MAPS_API_KEY not set (Google Maps features will be disabled)")
    else:
        print("   ✅ Google Maps API key configured")
    
    # Check Twilio
    if not settings.twilio.twilio_account_sid:
        warnings.append("⚠️  TWILIO_ACCOUNT_SID not set (Phone calling will be disabled)")
    else:
        print("   ✅ Twilio credentials configured")
    
    # Check phone scraping
    if not settings.phone_scraping.phone_scraping_enabled:
        warnings.append("⚠️  Phone scraping is disabled")
    else:
        print("   ✅ Phone scraping enabled")
    
    # Check geo-location
    if not settings.geolocation.geolocation_enabled:
        warnings.append("⚠️  Geo-location is disabled")
    else:
        print("   ✅ Geo-location enabled")
    
    # 2. Check database models
    print("\n2. Checking Database Models...")
    try:
        from core.database.models import TeamAgentRequest, TeamChatMessage
        print("   ✅ TeamAgentRequest model imported")
        print("   ✅ TeamChatMessage model imported")
    except ImportError as e:
        errors.append(f"❌ Failed to import database models: {e}")
    
    # 3. Check services
    print("\n3. Checking Services...")
    
    # Voice I/O Service
    try:
        from core.voice.voice_service import VoiceIOService
        print("   ✅ VoiceIOService imported")
    except ImportError as e:
        errors.append(f"❌ Failed to import VoiceIOService: {e}")
    
    # Phone Scraping Service
    try:
        from core.services.phone_scraping_service import PhoneScrapingService
        print("   ✅ PhoneScrapingService imported")
    except ImportError as e:
        errors.append(f"❌ Failed to import PhoneScrapingService: {e}")
    
    # Phone Calling Service
    try:
        from core.services.phone_calling_service import PhoneCallingService
        print("   ✅ PhoneCallingService imported")
    except ImportError as e:
        errors.append(f"❌ Failed to import PhoneCallingService: {e}")
    
    # Google Maps Service
    try:
        from core.services.google_maps_service import GoogleMapsService
        print("   ✅ GoogleMapsService imported")
    except ImportError as e:
        errors.append(f"❌ Failed to import GoogleMapsService: {e}")
    
    # Geo-location Service
    try:
        from core.services.geolocation_service import GeolocationService
        print("   ✅ GeolocationService imported")
    except ImportError as e:
        errors.append(f"❌ Failed to import GeolocationService: {e}")
    
    # Team Agent Processor
    try:
        from core.services.team_agent_processor import TeamAgentProcessor
        print("   ✅ TeamAgentProcessor imported")
    except ImportError as e:
        errors.append(f"❌ Failed to import TeamAgentProcessor: {e}")
    
    # 4. Check routers
    print("\n4. Checking Routers...")
    
    routers = [
        ("team_agent_router", "core.user_management.team_agent_router"),
        ("team_chat_router", "core.user_management.team_chat_router"),
        ("user_admin_router", "core.user_management.user_admin_router"),
        ("voice_router", "core.voice.voice_router"),
        ("phone_router", "core.services.phone_router"),
        ("google_maps_router", "core.services.google_maps_router"),
        ("geolocation_router", "core.services.geolocation_router"),
    ]
    
    for router_name, router_path in routers:
        try:
            module = __import__(router_path, fromlist=[router_name])
            print(f"   ✅ {router_name} imported")
        except ImportError as e:
            errors.append(f"❌ Failed to import {router_name}: {e}")
    
    # 5. Check agent voice mapping
    print("\n5. Checking Agent Voice Mapping...")
    try:
        from core.ai.agent_voice_mapping import AgentVoiceMapping
        mapping = AgentVoiceMapping()
        agents = ["aria", "clara", "eric", "jackie", "joe", "purity", "shakes"]
        for agent in agents:
            voice_config = mapping.get_agent_voice(agent)
            if voice_config:
                print(f"   ✅ {agent.capitalize()} voice: {voice_config['voice']} ({voice_config['gender']})")
            else:
                warnings.append(f"⚠️  No voice mapping for {agent}")
    except Exception as e:
        errors.append(f"❌ Failed to check agent voice mapping: {e}")
    
    # 6. Check migration file
    print("\n6. Checking Migration File...")
    migration_file = backend_path / "migrations" / "add_team_agent_requests.py"
    if migration_file.exists():
        print("   ✅ Migration file exists")
    else:
        errors.append("❌ Migration file not found: migrations/add_team_agent_requests.py")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ Errors Found: {len(errors)}")
        for error in errors:
            print(f"   {error}")
        print("\n⚠️  Please fix these errors before starting the server!")
        return False
    
    if warnings:
        print(f"\n⚠️  Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"   {warning}")
        print("\n💡 These are optional - features will be disabled if not configured")
    
    print("\n✅ Setup verification completed!")
    print("\n📝 Next Steps:")
    print("   1. Run migration: python backend/migrations/add_team_agent_requests.py")
    print("   2. Configure API keys in .env file (optional)")
    print("   3. Start the server: python backend/main.py")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_setup())
    sys.exit(0 if success else 1)

