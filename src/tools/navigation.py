import asyncio
from typing import Any, Dict, List
import json
import threading

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from browser.manager import BrowserManager
from utils.logger import logger
from utils.a11y_tree import find_working_node, extract_information_blocks
from services.tools_cache_manager import ElementsCacheManager


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

    async def _arun(self, url: str) -> str:
        """
        Navigate to the specified URL asynchronously.
        """
        
        page = self.browser_manager.current_page 
        if not page:
            return "Error: Browser not connected."
        
        if not url.startswith(('http://', 'https://')):
            return "Error: URL must start with http:// or https://"
        
        try:
            pages_map = {page.url: page for page in self.browser_manager._context.pages}

            if url in pages_map:
                opened_page = pages_map[url]
            else:
                # Playwright Async Context Manager
                async with self.browser_manager._context.expect_page() as new_page_info:
                    await page.evaluate('window.open("about:blank", "_blank")')
                opened_page = await new_page_info.value
                
            await opened_page.bring_to_front()
            self.browser_manager.current_page = opened_page
            response = await opened_page.goto(
                url, 
                wait_until="domcontentloaded", 
            )
            title = await opened_page.title()
            current_url = opened_page.url
            
            if response and response.status >= 400:
                return f"Warning: Status {response.status}. URL: {current_url}"
            
            return f"Successfully opened: '{title}'"
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Error opening page: {str(e)}"
    
    def _run(self, url: str) -> str:
        """
        Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Success message with page title and URL
        """
        raise RuntimeError("SYNCHRONOUS VERSION WAS RUN")
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
            self.browser_manager.current_page.on(
                "domcontentloaded", 
                ElementsCacheManager().track_dom_changes
            )

            response = opened_page.goto(
                url, 
                wait_until="domcontentloaded", 
            )
            
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
    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager,
    )
    
    def _arun(self, query: str) -> str:
        """Asynchronous version (not used)."""
        raise NotImplementedError("Use async version")
    
    def _run(self, query: str) -> str:
        """
        Search Google for the query and return first 7 results.
        
        Args:
            query: The search query
            
        Returns:
            JSON string with list of 7 search results (title, link, description)
        """
        logger.info(f"Searching Google for: {query}")
        
        page = self.browser_manager.current_page
        if not page:
            return "Error: Browser not connected."
        
        try:
            # Navigate to Google
            page.goto("https://www.google.com", wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            logger.info("Navigated to Google")
            
            # Find search input field using various selectors
            search_input = None
            search_selectors = [
                'textarea[name="q"]',  # New Google search box
                'input[name="q"]',     # Classic search box
                'textarea[title*="Search"]',
                'input[title*="Search"]',
            ]
            
            for selector in search_selectors:
                try:
                    search_input = page.locator(selector).first
                    if search_input.count() > 0 and search_input.is_visible():
                        break
                except:
                    continue
            
            if not search_input or search_input.count() == 0:
                return "Error: Could not find Google search input field"
            
            search_input.click()
            logger.info("Focused on search input")
            
            for char in query:
                search_input.type(char, delay=50)
            
            logger.info(f"Typed query: {query}")
            search_input.press("Enter")

            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            
            logger.info("Search results page loaded")
            
            # Extract results from accessibility tree
            try:
                accessibility_tree = page.accessibility.snapshot()
                
                results = self._extract_search_results_from_tree(accessibility_tree)
                
                results = results[:7]
                
                logger.info(f"Extracted {len(results)} search results")
                
                return json.dumps(results, indent=2)
                
            except Exception as e:
                logger.error(f"Error extracting search results: {e}")
                return f"Error extracting search results: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            return f"Error searching Google: {str(e)}"
    
    @staticmethod
    def _extract_search_results_from_tree(
            tree_node: Dict[str, Any], 
        ) -> List[Dict[str, Any]]:
        node = find_working_node(tree_node)  # the one wil will search for actual results in
        inf_blocks = extract_information_blocks(node)

        pass


def create_navigation_tools() -> list[BaseTool]:
    """
    Create all navigation-related tools.
    
    Args:
        browser_manager: The browser manager instance
        
    Returns:
        List of navigation tools
    """
    return [
        # SearchGoogleTool(),  - usage is deprecated asunderdeveloped
        OpenPageTool(),
    ]
