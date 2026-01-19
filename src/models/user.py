"""
Pydantic models for user preferences and confirmation requests.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class UserPreferences(BaseModel):
    """
    User preferences and commonly used information.
    """
    # Contact Information
    email: Optional[EmailStr] = Field(
        default=None,
        description="User's primary email address"
    )
    phone: Optional[str] = Field(
        default=None,
        description="User's phone number"
    )
    
    # Location
    address: Optional[str] = Field(
        default=None,
        description="User's primary address"
    )
    city: Optional[str] = Field(
        default=None,
        description="User's city"
    )
    
    # Preferences
    favorite_restaurants: List[str] = Field(
        default_factory=list,
        description="List of favorite restaurants or food places"
    )
    preferred_payment_method: Optional[str] = Field(
        default=None,
        description="Preferred payment method (for UI selection, not storage)"
    )
    
    # Contacts
    contacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of contact names to email addresses"
    )
    
    # Custom preferences
    custom_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional user-specific data"
    )
    
    def get_contact_email(self, name: str) -> Optional[str]:
        """
        Get email address for a contact by name (case-insensitive).
        
        Args:
            name: Contact name to look up
            
        Returns:
            Email address if found, None otherwise
        """
        # TODO: Implement fuzzy name matching
        pass
    
    def add_contact(self, name: str, email: str) -> None:
        """
        Add a new contact.
        
        Args:
            name: Contact name
            email: Contact email address
        """
        # TODO: Implement contact addition with validation
        pass


class ConfirmationRequest(BaseModel):
    """
    Request for user confirmation of a sensitive action.
    """
    action_description: str = Field(
        description="Clear description of what action will be taken"
    )
    reason: str = Field(
        description="Why this action is being requested"
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Potential risks or concerns"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details about the action"
    )
    
    def format_for_user(self) -> str:
        """
        Format the confirmation request as a user-friendly message.
        
        Returns:
            Formatted confirmation message
        """
        # TODO: Implement pretty formatting
        pass


class UserResponse(BaseModel):
    """
    User's response to a confirmation request or question.
    """
    confirmed: bool = Field(
        description="Whether the user confirmed the action"
    )
    message: Optional[str] = Field(
        default=None,
        description="Additional message from the user"
    )
    modifications: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any modifications requested by the user"
    )
