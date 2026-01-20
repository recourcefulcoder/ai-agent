"""
Navigation-related tools for the agent.
Handles URL navigation, Google search, and page transitions.
"""

from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from browser.manager import BrowserManager
from utils.logger import logger


class NavigateInput(BaseModel):
    """Input schema for navigate_to_url tool."""
    url: str = Field(description="The URL to navigate to (must include http:// or https://)")


class SearchInput(BaseModel):
    """Input schema for search_google tool."""
    query: str = Field(description="The search query")


class OpenPageInput(BaseModel):
    """Input schema for opening a new page."""
    url: str = Field(
        description="The URL of the page to open (must include http:// or https://)"
    )


class OpenPageTool(BaseTool):
    """
    Tool for navigating to a new URL in the current browser session.
    """
    
    name: str = "open_page"
    description: str = """
    Open a new page (navigate to a URL) in the current browser session.
    The URL must include the protocol (http:// or https://).
    
    Example: open_page(url="https://www.google.com")
    """
    args_schema: type[BaseModel] = OpenPageInput
    browser_manager: BrowserManager = Field(exclude=True)
    
    def _run(self, url: str) -> str:
        """
        Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Success message with page title and URL
        """
        logger.info(f"Navigating to: {url}")
        
        page = self.browser_manager.current_page
        if not page:
            return "Error: Browser not connected."
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return "Error: URL must start with http:// or https://"
        
        try:
            # Navigate to the URL
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for page to be ready
            page.wait_for_load_state("domcontentloaded")
            
            # Get page title
            title = page.title()
            current_url = page.url
            
            logger.info(f"Successfully navigated to: {current_url}")
            
            # Check if navigation was successful
            if response and response.status >= 400:
                return f"Warning: Page loaded with status {response.status}. URL: {current_url}, Title: '{title}'"
            
            return f"Successfully opened page: '{title}' at {current_url}"
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return f"Error opening page: {str(e)}"


class NavigateToURLTool(BaseTool):
    """
    Tool for navigating to a specific URL.
    """
    
    name: str = "navigate_to_url"
    description: str = """
    Navigate the browser to a specific URL.
    Use this when you know the exact URL you want to visit.
    The URL must include the protocol (http:// or https://).
    
    Example: navigate_to_url(url="https://www.google.com")
    """
    args_schema: type[BaseModel] = NavigateInput
    browser_manager: BrowserManager = Field(exclude=True)
    
    def _run(self, url: str) -> str:
        """
        Synchronous version (not used, but required by BaseTool).
        """
        raise NotImplementedError("Use async version")
    
    async def _arun(self, url: str) -> str:
        """
        Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Success message with the page title and URL
        """
        logger.info(f"Navigating to: {url}")
        
        # TODO: Validate URL format
        # TODO: Get current page from browser manager
        # TODO: Navigate to URL with timeout
        # TODO: Wait for page to load (networkidle or domcontentloaded)
        # TODO: Get page title
        # TODO: Return success message with title and URL
        
        pass


class SearchGoogleTool(BaseTool):
    """
    Tool for searching Google.
    """
    
    name: str = "search_google"
    description: str = """
    Search Google for a query.
    Use this when you need to find information or websites.
    
    Example: search_google(query="best pizza near me")
    """
    args_schema: type[BaseModel] = SearchInput
    browser_manager: BrowserManager = Field(exclude=True)
    
    def _arun(self, query: str) -> str:
        """Asynchronous version (not used)."""
        raise NotImplementedError("Use async version")
    
    def _run(self, query: str) -> str:
        """
        Search Google for the query.
        
        Args:
            query: The search query
            
        Returns:
            Message indicating search was performed
        """
        logger.info(f"Searching Google for: {query}")
        
        # TODO: Navigate to Google
        # TODO: Find search input field
        # TODO: Type query into search field
        # TODO: Press Enter or click search button
        # TODO: Wait for results page to load
        # TODO: Return success message
        
        pass


def create_navigation_tools(browser_manager: BrowserManager) -> list[BaseTool]:
    """
    Create all navigation-related tools.
    
    Args:
        browser_manager: The browser manager instance
        
    Returns:
        List of navigation tools
    """
    return [
        NavigateToURLTool(browser_manager=browser_manager),
        SearchGoogleTool(browser_manager=browser_manager),
        OpenPageTool(browser_manager=browser_manager),
    ]
