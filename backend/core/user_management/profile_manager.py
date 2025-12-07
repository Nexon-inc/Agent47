import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
import re

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile data structure."""
    user_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    preferences: Dict[str, Any] = None
    social_links: Dict[str, str] = None
    skills: List[str] = None
    interests: List[str] = None
    created_at: str = None
    updated_at: str = None
    is_public: bool = True
    is_verified: bool = False

class ProfileManager:
    """Manages user profiles and related functionality."""
    
    def __init__(self):
        self.profiles: Dict[str, UserProfile] = {}
        # Defer loading profiles to avoid async DB access during import
        # Profiles will be populated on demand by application flows
        logger.info("ProfileManager initialized with deferred loading")
    
    def _load_profiles(self):
        """Load profiles from database."""
        try:
            # Skipping DB-backed profile load at startup to avoid blocking async initialization
            self.profiles = {}
            logger.info("Skipped profile load at startup (deferred)")
        except Exception as e:
            logger.error(f"Failed to initialize profiles map: {e}")
            self.profiles = {}
    
    def _save_profiles(self):
        """Save profiles to database."""
        try:
            # Skipping DB-backed profile persistence in this runtime path
            logger.info("Skipped saving profiles (no-op in current configuration)")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
    
    def create_profile(
        self,
        user_id: str,
        username: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """
        Create a new user profile.
        
        Args:
            user_id: Unique user ID
            username: Username for the profile
            email: Email address
            first_name: First name
            last_name: Last name
            **kwargs: Additional profile fields
            
        Returns:
            Created UserProfile object
        """
        try:
            # Validate input
            if not self._validate_email(email):
                raise ValueError("Invalid email format")
            
            if not self._validate_username(username):
                raise ValueError("Invalid username format")
            
            # Check if user already has a profile
            if user_id in self.profiles:
                raise ValueError(f"Profile already exists for user {user_id}")
            
            # Check if username is taken
            if any(p.username == username for p in self.profiles.values()):
                raise ValueError(f"Username {username} is already taken")
            
            # Create profile
            profile = UserProfile(
                user_id=user_id,
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                preferences=kwargs.get('preferences', {}),
                social_links=kwargs.get('social_links', {}),
                skills=kwargs.get('skills', []),
                interests=kwargs.get('interests', []),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                **{k: v for k, v in kwargs.items() if k not in ['preferences', 'social_links', 'skills', 'interests']}
            )
            
            self.profiles[user_id] = profile
            self._save_profiles()
            
            logger.info(f"Created profile for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create profile: {e}")
            raise
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile object or None if not found
        """
        try:
            return self.profiles.get(user_id)
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            return None
    
    def get_profile_by_username(self, username: str) -> Optional[UserProfile]:
        """
        Get user profile by username.
        
        Args:
            username: Username
            
        Returns:
            UserProfile object or None if not found
        """
        try:
            for profile in self.profiles.values():
                if profile.username == username:
                    return profile
            return None
        except Exception as e:
            logger.error(f"Failed to get profile by username: {e}")
            return None
    
    def update_profile(self, user_id: str, **updates) -> bool:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            **updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.profiles:
                return False
            
            profile = self.profiles[user_id]
            
            # Validate email if being updated
            if 'email' in updates and not self._validate_email(updates['email']):
                raise ValueError("Invalid email format")
            
            # Validate username if being updated
            if 'username' in updates:
                if not self._validate_username(updates['username']):
                    raise ValueError("Invalid username format")
                
                # Check if username is taken by another user
                for other_profile in self.profiles.values():
                    if (other_profile.user_id != user_id and 
                        other_profile.username == updates['username']):
                        raise ValueError(f"Username {updates['username']} is already taken")
            
            # Update fields
            for field, value in updates.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
            
            # Update timestamp
            profile.updated_at = datetime.utcnow().isoformat()
            
            self._save_profiles()
            
            logger.info(f"Updated profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return False
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Delete user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.profiles:
                return False
            
            del self.profiles[user_id]
            self._save_profiles()
            
            logger.info(f"Deleted profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete profile: {e}")
            return False
    
    def search_profiles(
        self,
        query: str,
        limit: int = 10,
        include_private: bool = False
    ) -> List[UserProfile]:
        """
        Search profiles by various criteria.
        
        Args:
            query: Search query
            limit: Maximum number of results
            include_private: Whether to include private profiles
            
        Returns:
            List of matching UserProfile objects
        """
        try:
            results = []
            query_lower = query.lower()
            
            for profile in self.profiles.values():
                # Skip private profiles unless requested
                if not include_private and not profile.is_public:
                    continue
                
                # Search in various fields
                searchable_fields = [
                    profile.username,
                    profile.first_name,
                    profile.last_name,
                    profile.bio,
                    profile.location
                ]
                
                # Add skills and interests
                if profile.skills:
                    searchable_fields.extend(profile.skills)
                if profile.interests:
                    searchable_fields.extend(profile.interests)
                
                # Check if query matches any field
                for field in searchable_fields:
                    if field and query_lower in field.lower():
                        results.append(profile)
                        break
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search profiles: {e}")
            return []
    
    def get_profile_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get profile statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with profile statistics
        """
        try:
            profile = self.get_profile(user_id)
            if not profile:
                return {}
            
            # Calculate profile completeness
            required_fields = ['username', 'email', 'first_name', 'last_name']
            optional_fields = ['bio', 'avatar_url', 'location', 'website', 'phone', 'skills', 'interests']
            
            completed_required = sum(1 for field in required_fields if getattr(profile, field))
            completed_optional = sum(1 for field in optional_fields if getattr(profile, field))
            
            total_required = len(required_fields)
            total_optional = len(optional_fields)
            
            completeness = {
                "required_completion": completed_required / total_required * 100,
                "optional_completion": completed_optional / total_optional * 100,
                "overall_completion": (completed_required + completed_optional) / (total_required + total_optional) * 100
            }
            
            return {
                "user_id": user_id,
                "username": profile.username,
                "completeness": completeness,
                "skills_count": len(profile.skills or []),
                "interests_count": len(profile.interests or []),
                "social_links_count": len(profile.social_links or {}),
                "is_public": profile.is_public,
                "is_verified": profile.is_verified,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get profile statistics: {e}")
            return {}
    
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.profiles:
                return False
            
            profile = self.profiles[user_id]
            profile.preferences.update(preferences)
            profile.updated_at = datetime.utcnow().isoformat()
            
            self._save_profiles()
            
            logger.info(f"Updated preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            return False
    
    def add_skill(self, user_id: str, skill: str) -> bool:
        """
        Add a skill to user profile.
        
        Args:
            user_id: User ID
            skill: Skill to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.profiles:
                return False
            
            profile = self.profiles[user_id]
            if profile.skills is None:
                profile.skills = []
            
            if skill not in profile.skills:
                profile.skills.append(skill)
                profile.updated_at = datetime.utcnow().isoformat()
                self._save_profiles()
                
                logger.info(f"Added skill '{skill}' to user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to add skill: {e}")
            return False
    
    def remove_skill(self, user_id: str, skill: str) -> bool:
        """
        Remove a skill from user profile.
        
        Args:
            user_id: User ID
            skill: Skill to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.profiles:
                return False
            
            profile = self.profiles[user_id]
            if profile.skills and skill in profile.skills:
                profile.skills.remove(skill)
                profile.updated_at = datetime.utcnow().isoformat()
                self._save_profiles()
                
                logger.info(f"Removed skill '{skill}' from user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove skill: {e}")
            return False
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format."""
        # Username should be 3-30 characters, alphanumeric and underscores only
        pattern = r'^[a-zA-Z0-9_]{3,30}$'
        return bool(re.match(pattern, username))
    
    def export_profile(self, user_id: str, format: str = "json") -> str:
        """
        Export user profile data.
        
        Args:
            user_id: User ID
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        try:
            profile = self.get_profile(user_id)
            if not profile:
                return ""
            
            if format.lower() == "json":
                return json.dumps(asdict(profile), indent=2)
            elif format.lower() == "csv":
                # Simple CSV export
                fields = ["user_id", "username", "email", "first_name", "last_name", "bio", "location"]
                values = [getattr(profile, field, "") for field in fields]
                return ",".join(f'"{value}"' for value in values)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export profile: {e}")
            return ""

# Global instance
profile_manager = ProfileManager()

def get_profile_manager() -> ProfileManager:
    """Get the global profile manager instance."""
    return profile_manager
