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


class SearchDuckDuckGoTool(BaseTool):
    name: str = "search_on_duckduckgo"
    description: str = (
        "Search using DuckDuckGo. Returns a list of results mapped to an 'element_id'. "
        "The agent can use this 'element_id' in subsequent steps to click on the link."
    )
    args_schema: Type[BaseModel] = SearchInput

    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager # Using lambda to defer instantiation if needed
    )

    def _run(self, query: str) -> List[Dict[str, str]]:
        """
        Synchronous execution using the persistent BrowserManager.
        """
        # 1. Retrieve the active page from your manager
        # Assuming your BrowserManager has a method like 'get_page()' or property 'page'
        # that returns a playwright.sync_api.Page object
        
        page = self.browser_manager.get_page()

        try:
            # 2. Navigate to DuckDuckGo HTML (Lite) version
            # We use the HTML version for faster, reliable, static selectors
            page.goto("https://html.duckduckgo.com/html/", wait_until="domcontentloaded")

            # 3. Perform Search
            page.fill('input[name="q"]', query)
            page.keyboard.press("Enter")

            # 4. Wait for results to appear
            page.wait_for_selector(".result", timeout=5000)

            # 5. Process Results & Inject IDs
            # We fetch all result containers
            result_locators = page.locator(".result").all()
            
            parsed_results = []

            # We limit to top 10 to save tokens
            for index, row_locator in enumerate(result_locators[:10]):
                
                # Locate the anchor tag (link) within the result row
                link_locator = row_locator.locator(".result__a").first
                snippet_locator = row_locator.locator(".result__snippet").first

                if link_locator.count() > 0:
                    # A. Generate a unique ID for this session
                    element_id = f"search_result_{index}"

                    # B. DOM MANIPULATION: 
                    # We inject this ID directly into the HTML 'id' attribute of the <a> tag.
                    # This ensures that standard 'click' tools can target it easily via CSS selector.
                    link_locator.evaluate(f"el => el.setAttribute('id', '{element_id}')")

                    # C. Extract Text Data
                    title = link_locator.text_content().strip()
                    href = link_locator.get_attribute("href")
                    snippet = snippet_locator.text_content().strip() if snippet_locator.count() > 0 else ""

                    parsed_results.append({
                        "element_id": element_id, # Agent uses this to click
                        "title": title,
                        "link": href,
                        "description": snippet
                    })

            return parsed_results

        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    def _arun(self, query: str):
        raise NotImplementedError("This tool is strictly synchronous.")


def create_navigation_tools(browser_manager: BrowserManager) -> list[BaseTool]:
    """
    Create all navigation-related tools.
    
    Args:
        browser_manager: The browser manager instance
        
    Returns:
        List of navigation tools
    """
    return [
        SearchDuckDuckGoTool(),
        OpenPageTool(),
    ]
