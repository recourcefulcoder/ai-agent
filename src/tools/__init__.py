"""
Tools module for browser AI agent.
"""

from tools.navigation import create_navigation_tools
from tools.interaction import create_interaction_tools
from tools.analysis import create_analysis_tools
from tools.user import create_user_tools


def get_all_tools():
    """
    Get all available tools for the agent.
    
    Returns:
        List of all LangChain tools
    """
    return (
        create_navigation_tools() +
        create_interaction_tools() +
        create_analysis_tools() +
        create_user_tools()
    )


__all__ = [
    'get_all_tools',
    'create_navigation_tools',
    'create_interaction_tools',
    'create_analysis_tools',
    'create_user_tools',
]
