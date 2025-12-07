#!/usr/bin/env python3
"""
Test script for password reset functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.authentication.auth_manager import auth_manager
from core.config import settings

async def test_password_reset():
    """Test the password reset functionality"""
    print("Testing Password Reset Functionality")
    print("=" * 50)
    
    # Test email
    test_email = "test@example.com"
    
    print(f"1. Testing password reset request for: {test_email}")
    
    try:
        # Test password reset request
        success = await auth_manager.reset_password_request(test_email)
        
        if success:
            print("✅ Password reset request successful")
            print("   - Check backend logs for reset URL (if SMTP not configured)")
            print("   - Check email inbox (if SMTP is configured)")
        else:
            print("❌ Password reset request failed")
            
    except Exception as e:
        print(f"❌ Error during password reset request: {e}")
    
    print("\n2. Email Configuration Status:")
    print(f"   - SMTP Host: {settings.email.smtp_host}")
    print(f"   - SMTP Port: {settings.email.smtp_port}")
    print(f"   - From Email: {settings.email.from_email}")
    print(f"   - From Name: {settings.email.from_name}")
    print(f"   - SMTP Username: {settings.email.smtp_username}")
    print(f"   - SMTP Password: {'***' if settings.email.smtp_password else 'Not set'}")
    print(f"   - Use TLS: {settings.email.use_tls}")
    
    if not settings.email.smtp_password:
        print("\n⚠️  SMTP password not configured!")
        print("   - Set EMAIL_SMTP_PASSWORD environment variable")
        print("   - Or add it to your .env file")
        print("   - Reset URLs will be logged to console instead")
    
    print("\n3. Frontend URL:")
    print(f"   - Reset page: {settings.frontend_url}/auth/reset-password")
    
    print("\n4. Testing Instructions:")
    print("   1. Start the backend server: python -m uvicorn main:app --reload")
    print("   2. Start the frontend: npm run dev")
    print("   3. Go to http://localhost:3000/auth")
    print("   4. Click 'Login' tab")
    print("   5. Click 'Forgot password?'")
    print("   6. Enter your email address")
    print("   7. Check backend logs for reset URL or check your email")
    print("   8. Use the reset URL to reset your password")

if __name__ == "__main__":
    asyncio.run(test_password_reset())
