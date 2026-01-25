import json
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet

from models.user import UserPreferences
from config.settings import settings
from utils.logger import logger


class UserProfileService:
    """
    Service for managing user profile and preferences.
    """
    
    def __init__(self):
        self.profile_path = Path(settings.user_profile_path)
        self._encryption_key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
        
        # Initialize encryption if enabled
        if settings.encrypt_user_data:
            self._init_encryption()
    
    def _init_encryption(self) -> None:
        """
        Initialize encryption key.
        In production, this should be stored securely (e.g., system keychain).
        """
        key_path = self.profile_path.parent / ".encryption_key"
        
        # TODO: Load or generate encryption key
        # TODO: Store key securely (not in plain text!)
        # TODO: Initialize Fernet cipher
        
        pass
    
    def load_profile(self) -> UserPreferences:
        """
        Load user profile from disk.
        
        Returns:
            UserPreferences object
        """
        if not self.profile_path.exists():
            logger.info("No existing profile found, creating new one")
            return UserPreferences()
        
        try:
            # TODO: Read file
            # TODO: Decrypt if encryption enabled
            # TODO: Parse JSON
            # TODO: Create UserPreferences instance
            
            with open(self.profile_path, 'r') as f:
                data = json.load(f)
            
            return UserPreferences(**data)
        
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return UserPreferences()
    
    def save_profile(self, profile: UserPreferences) -> None:
        """
        Save user profile to disk.
        
        Args:
            profile: UserPreferences to save
        """
        try:
            # Ensure directory exists
            self.profile_path.parent.mkdir(parents=True, exist_ok=True)
            
            # TODO: Convert to dict
            # TODO: Serialize to JSON
            # TODO: Encrypt if enabled
            # TODO: Write to file
            
            with open(self.profile_path, 'w') as f:
                json.dump(profile.model_dump(), f, indent=2)
            
            logger.info(f"Profile saved to {self.profile_path}")
        
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
    
    def update_profile(self, **kwargs) -> UserPreferences:
        """
        Update specific fields in the profile.
        
        Args:
            **kwargs: Fields to update
            
        Returns:
            Updated UserPreferences
        """
        # TODO: Load current profile
        # TODO: Update fields
        # TODO: Save profile
        # TODO: Return updated profile
        
        pass
    
    def add_contact(self, name: str, email: str) -> None:
        """
        Add a contact to the profile.
        
        Args:
            name: Contact name
            email: Contact email
        """
        # TODO: Load profile
        # TODO: Add contact
        # TODO: Save profile
        
        pass


# Global service instance
_user_profile_service: Optional[UserProfileService] = None


def get_user_profile_service() -> UserProfileService:
    """
    Get or create the user profile service singleton.
    
    Returns:
        UserProfileService instance
    """
    global _user_profile_service
    if _user_profile_service is None:
        _user_profile_service = UserProfileService()
    return _user_profile_service
