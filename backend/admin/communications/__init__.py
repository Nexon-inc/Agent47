from .communication_manager import CommunicationManager
from .email_service import EmailService
from .sms_service import SMSService
from .template_manager import TemplateManager

# NotificationService doesn't exist yet, importing from notification_manager if available
try:
    from .notification_manager import NotificationService
except ImportError:
    # Create a stub if it doesn't exist
    class NotificationService:
        pass

__all__ = [
    "CommunicationManager",
    "EmailService", 
    "SMSService",
    "NotificationService",
    "TemplateManager"
]
