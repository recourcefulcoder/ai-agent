"""
User preference and profile tools.
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from services.user_profile import get_user_profile_service
from utils.logger import logger


class GetUserPreferenceInput(BaseModel):
    """Input schema for getting user preferences."""
    preference_key: str = Field(
        description="The preference key to retrieve (e.g., 'email', 'address', 'favorite_pizza_place')"
    )


class GetUserPreferenceTool(BaseTool):
    """
    Tool for retrieving user preferences and profile data.
    """
    
    name: str = "get_user_preference"
    description: str = """
    Get a user preference or profile data by key.
    Use this when you need user-specific information like email, address, favorite places, etc.
    
    Example: get_user_preference(preference_key="email")
    """
    args_schema: type[BaseModel] = GetUserPreferenceInput
    
    def _run(self, preference_key: str) -> str:
        """
        Get a user preference value.
        
        Args:
            preference_key: The preference key to retrieve
            
        Returns:
            The preference value or error message
        """
        logger.info(f"Retrieving user preference: {preference_key}")
        
        try:
            user_profile_service = get_user_profile_service()
            profile = user_profile_service.load_profile()
            
            # Try to get the preference from profile
            value = getattr(profile, preference_key, None)
            
            if value is None:
                return f"User preference '{preference_key}' not found. Please ask the user for this information."
            
            logger.info(f"Retrieved preference: {preference_key}")
            return str(value)
            
        except Exception as e:
            logger.error(f"Error retrieving user preference: {e}")
            return f"Error retrieving user preference: {str(e)}"


def create_user_tools() -> list[BaseTool]:
    """
    Create all user-related tools.
    
    Returns:
        List of user tools
    """
    return [
        GetUserPreferenceTool(),
    ]
