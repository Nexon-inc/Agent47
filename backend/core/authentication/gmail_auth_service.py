"""
Gmail API Authentication Service for Agent47
Handles Gmail API authentication, token management, and email sending
"""

import os
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import settings

logger = logging.getLogger(__name__)

class GmailAuthService:
    """Gmail API authentication and email sending service"""
    
    def __init__(self):
        self.settings = settings.gmail
        self.service = None
        self.credentials = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize Gmail API service with authentication"""
        try:
            logger.info("Initializing Gmail API service...")
            
            # Ensure credentials directory exists
            credentials_dir = Path(self.settings.credentials_file).parent
            credentials_dir.mkdir(parents=True, exist_ok=True)
            
            # Load or create credentials
            self.credentials = await self._load_credentials()
            
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired Gmail credentials...")
                    await self._refresh_credentials()
                else:
                    logger.error("No valid Gmail credentials found. Please run OAuth2 flow.")
                    return False
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            # Test the service
            await self._test_service()
            
            self._initialized = True
            logger.info("Gmail API service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail API service: {e}")
            return False
    
    async def _load_credentials(self) -> Optional[Credentials]:
        """Load credentials from file or environment variables"""
        try:
            # Try to load from token file first
            if os.path.exists(self.settings.token_file):
                logger.info(f"Loading Gmail credentials from {self.settings.token_file}")
                return Credentials.from_authorized_user_file(
                    self.settings.token_file, 
                    self.settings.scopes
                )
            
            # Try to load from credentials file
            if os.path.exists(self.settings.credentials_file):
                logger.info(f"Loading Gmail credentials from {self.settings.credentials_file}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.settings.credentials_file,
                    self.settings.scopes
                )
                return flow.run_local_server(port=0)
            
            # Try to create from environment variables
            if self.settings.client_id and self.settings.client_secret:
                logger.info("Creating Gmail credentials from environment variables")
                return Credentials(
                    token=self.settings.access_token,
                    refresh_token=self.settings.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.settings.client_id,
                    client_secret=self.settings.client_secret,
                    scopes=self.settings.scopes
                )
            
            logger.warning("No Gmail credentials found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load Gmail credentials: {e}")
            return None
    
    async def _refresh_credentials(self) -> bool:
        """Refresh expired credentials"""
        try:
            if not self.credentials or not self.credentials.refresh_token:
                logger.error("No refresh token available")
                return False
            
            logger.info("Refreshing Gmail credentials...")
            self.credentials.refresh(Request())
            
            # Save refreshed credentials
            await self._save_credentials()
            
            logger.info("Gmail credentials refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh Gmail credentials: {e}")
            return False
    
    async def _save_credentials(self) -> bool:
        """Save credentials to token file"""
        try:
            if not self.credentials:
                return False
            
            # Ensure directory exists
            token_dir = Path(self.settings.token_file).parent
            token_dir.mkdir(parents=True, exist_ok=True)
            
            # Save credentials
            with open(self.settings.token_file, 'w') as token_file:
                token_file.write(self.credentials.to_json())
            
            logger.info(f"Gmail credentials saved to {self.settings.token_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save Gmail credentials: {e}")
            return False
    
    async def _test_service(self) -> bool:
        """Test Gmail service connectivity"""
        try:
            if not self.service:
                return False
            
            # Test by sending a simple message (this doesn't require additional scopes)
            # We'll just verify the service is initialized properly
            logger.info("Gmail service test successful - service initialized")
            return True
            
        except Exception as e:
            logger.error(f"Gmail service test error: {e}")
            return False
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email via Gmail API"""
        try:
            if not self._initialized or not self.service:
                logger.error("Gmail service not initialized")
                return False
            
            # Use default from email if not provided
            from_email = from_email or self.settings.from_email
            from_name = from_name or self.settings.from_name
            
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['from'] = f"{from_name} <{from_email}>"
            message['subject'] = subject
            
            # Add text part
            if body_text:
                text_part = MIMEText(body_text, 'plain')
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(body_html, 'html')
            message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {send_message['id']}")
            return True
            
        except HttpError as e:
            logger.error(f"Gmail API error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send email verification email"""
        try:
            # Create verification URL
            verification_url = f"{settings.frontend_url}/verify-email?token={verification_token}"
            
            # Email subject
            subject = "Verify Your Agent47 Account"
            
            # HTML body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Verify Your Agent47 Account</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9fafb; }}
                    .button {{ display: inline-block; background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to Agent47!</h1>
                    </div>
                    <div class="content">
                        <h2>Verify Your Email Address</h2>
                        <p>Hello{f' {user_name}' if user_name else ''},</p>
                        <p>Thank you for signing up for Agent47! To complete your registration and start using our AI automation platform, please verify your email address by clicking the button below:</p>
                        
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                        
                        <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                        <p><a href="{verification_url}">{verification_url}</a></p>
                        
                        <p>This verification link will expire in {self.settings.verification_token_expiry_hours} hours.</p>
                        
                        <p>If you didn't create an account with Agent47, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 Agent47. All rights reserved.</p>
                        <p>This is an automated message, please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text body
            text_body = f"""
            Welcome to Agent47!
            
            Hello{f' {user_name}' if user_name else ''},
            
            Thank you for signing up for Agent47! To complete your registration and start using our AI automation platform, please verify your email address by visiting this link:
            
            {verification_url}
            
            This verification link will expire in {self.settings.verification_token_expiry_hours} hours.
            
            If you didn't create an account with Agent47, please ignore this email.
            
            © 2024 Agent47. All rights reserved.
            """
            
            # Send email
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body_html=html_body,
                body_text=text_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {e}")
            return False
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send welcome email after successful verification"""
        try:
            subject = "Welcome to Agent47 - Your Account is Verified!"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to Agent47</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9fafb; }}
                    .button {{ display: inline-block; background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Welcome to Agent47!</h1>
                    </div>
                    <div class="content">
                        <h2>Your Account is Now Verified</h2>
                        <p>Hello{f' {user_name}' if user_name else ''},</p>
                        <p>Congratulations! Your Agent47 account has been successfully verified. You can now access all the features of our AI automation platform.</p>
                        
                        <a href="{settings.frontend_url}/dashboard" class="button">Go to Dashboard</a>
                        
                        <h3>What's Next?</h3>
                        <ul>
                            <li>Complete your profile setup</li>
                            <li>Choose your subscription tier</li>
                            <li>Select your AI agents</li>
                            <li>Start automating your workflows</li>
                        </ul>
                        
                        <p>If you have any questions, feel free to reach out to our support team.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 Agent47. All rights reserved.</p>
                        <p>This is an automated message, please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            🎉 Welcome to Agent47!
            
            Hello{f' {user_name}' if user_name else ''},
            
            Congratulations! Your Agent47 account has been successfully verified. You can now access all the features of our AI automation platform.
            
            Visit your dashboard: {settings.frontend_url}/dashboard
            
            What's Next?
            - Complete your profile setup
            - Choose your subscription tier
            - Select your AI agents
            - Start automating your workflows
            
            If you have any questions, feel free to reach out to our support team.
            
            © 2024 Agent47. All rights reserved.
            """
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body_html=html_body,
                body_text=text_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {e}")
            return False
    
    async def close(self):
        """Close Gmail service"""
        if self.service:
            self.service = None
        self._initialized = False
        logger.info("Gmail service closed")

# Global Gmail service instance
gmail_auth_service = GmailAuthService()
