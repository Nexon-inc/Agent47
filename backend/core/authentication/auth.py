from core.authentication.auth_manager import get_current_user, get_current_active_user

# Compatibility shim: some modules import core.authentication.auth.get_current_user
# Re-export the functions from auth_manager for backwards compatibility.

__all__ = ["get_current_user", "get_current_active_user"]
