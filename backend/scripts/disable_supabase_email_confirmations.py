"""
Script to help disable Supabase email confirmations
This script provides instructions and can help verify the configuration
"""

import os
import requests
import json
from pathlib import Path

def check_supabase_config():
    """Check current Supabase configuration"""
    print("🔍 Checking Supabase Configuration...")
    print("=" * 50)
    
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    # Read .env file
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    
    supabase_url = env_vars.get('SUPABASE_URL')
    supabase_service_key = env_vars.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase configuration in .env file")
        print("Required variables:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ Service Key: {'*' * 20}{supabase_service_key[-10:]}")
    
    return True

def get_supabase_auth_settings():
    """Get current Supabase auth settings"""
    print("\n🔍 Checking Supabase Auth Settings...")
    print("=" * 50)
    
    env_path = Path(__file__).parent.parent.parent / ".env"
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    
    supabase_url = env_vars.get('SUPABASE_URL')
    supabase_service_key = env_vars.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase configuration")
        return None
    
    # Try to get auth settings
    try:
        headers = {
            'apikey': supabase_service_key,
            'Authorization': f'Bearer {supabase_service_key}',
            'Content-Type': 'application/json'
        }
        
        # Get auth settings
        response = requests.get(
            f"{supabase_url}/auth/v1/settings",
            headers=headers
        )
        
        if response.status_code == 200:
            settings = response.json()
            print("✅ Current Auth Settings:")
            print(f"   - Email Confirmations: {settings.get('enable_signup', 'Unknown')}")
            print(f"   - Email Change Confirmations: {settings.get('enable_email_change_confirmations', 'Unknown')}")
            return settings
        else:
            print(f"❌ Failed to get auth settings: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting auth settings: {e}")
        return None

def provide_manual_instructions():
    """Provide manual instructions to disable email confirmations"""
    print("\n📋 Manual Instructions to Disable Supabase Email Confirmations")
    print("=" * 70)
    print()
    print("Since we can't automatically modify Supabase settings, please follow these steps:")
    print()
    print("1. 🌐 Go to your Supabase Dashboard:")
    print("   https://supabase.com/dashboard")
    print()
    print("2. 📁 Select your project")
    print()
    print("3. 🔐 Navigate to Authentication → Settings")
    print()
    print("4. 📧 Under 'Email Confirmation' section:")
    print("   - Turn OFF 'Enable email confirmations'")
    print("   - Turn OFF 'Enable email change confirmations' (if present)")
    print()
    print("5. 💾 Click 'Save' to apply changes")
    print()
    print("6. ✅ Verify the changes are saved")
    print()
    print("This will prevent Supabase from sending its own verification emails,")
    print("allowing our Gmail API integration to handle email verification instead.")

def main():
    """Main function"""
    print("🚀 Supabase Email Confirmation Disabler")
    print("=" * 50)
    
    # Check configuration
    if not check_supabase_config():
        return
    
    # Try to get current settings
    settings = get_supabase_auth_settings()
    
    # Provide manual instructions
    provide_manual_instructions()
    
    print("\n🎯 Next Steps:")
    print("1. Follow the manual instructions above")
    print("2. Restart your backend server")
    print("3. Test the signup flow")
    print("4. Verify that Gmail API sends verification emails instead of Supabase")

if __name__ == "__main__":
    main()
