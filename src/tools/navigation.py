from typing import Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from browser.manager import BrowserManager
from utils.logger import logger


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
    Open a new tab (navigate to a URL) in the current browser session, or activate tab if it has already been opened during the session.
    The URL must include the protocol (http:// or https://). 
    
    Example: open_page(url="https://www.google.com")
    """
    args_schema: type[BaseModel] = OpenPageInput
    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager,
    )
    
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
        
        if not url.startswith(('http://', 'https://')):
            return "Error: URL must start with http:// or https://"
        
        try:
            pages_map = {page.url: page for page in self.browser_manager._context.pages}

            if url in pages_map.keys():
                opened_page = pages_map[url]
            else:
                with self.browser_manager._context.expect_page() as new_page_info:
                    page.evaluate('window.open("about:blank", "_blank")')
                opened_page = new_page_info.value
            opened_page.bring_to_front()
            self.browser_manager.current_page = opened_page

            response = opened_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            
            title = page.title()
            current_url = page.url
            
            logger.info(f"Successfully navigated to: {current_url}")
            
            if response and response.status >= 400:
                return f"Warning: Page loaded with status {response.status}. URL: {current_url}, Title: '{title}'"
            
            return f"Successfully opened page: '{title}' at {current_url}"
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return f"Error opening page: {str(e)}"


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
        SearchGoogleTool(),
        OpenPageTool(),
    ]
