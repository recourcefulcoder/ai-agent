from typing import Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from browser.manager import BrowserManager
from utils.logger import logger
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
            self.browser_manager.current_page.on(
                "domcontentloaded", 
                ElementsCacheManager().track_dom_changes
            )

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
                
                if not accessibility_tree:
                    return "Error: Could not get accessibility tree"
                
                # Find the main content area
                results = self._extract_search_results_from_tree(accessibility_tree, query)
                
                if not results:
                    # Fallback: try to extract from DOM
                    results = self._extract_search_results_from_dom(page)
                
                # Limit to 7 results
                results = results[:7]
                
                logger.info(f"Extracted {len(results)} search results")
                
                if not results:
                    return "No search results found"
                
                return json.dumps(results, indent=2)
                
            except Exception as e:
                logger.error(f"Error extracting search results: {e}")
                return f"Error extracting search results: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            return f"Error searching Google: {str(e)}"
    
    def _extract_search_results_from_tree(self, tree_node: dict, query: str) -> list:
        """Extract search results from accessibility tree."""
        results = []
        
        def traverse(node, in_main=False):
            role = node.get('role', '')
            name = node.get('name', '')
            
            # Check if we're in the main content area
            if role == 'main':
                in_main = True
            
            # Look for links in main area that appear to be search results
            if in_main and role == 'link' and name:
                # Try to extract description from children or siblings
                description = ""
                
                # Check if parent has more info
                children = node.get('children', [])
                for child in children:
                    child_name = child.get('name', '')
                    if child_name and child_name != name:
                        description = child_name[:50]
                        break
                
                # Avoid duplicate results and filter out common navigation links
                common_excludes = ['Images', 'Videos', 'News', 'Maps', 'Shopping', 
                                 'More', 'Settings', 'Tools', 'Sign in', query]
                
                if name not in [r['title'] for r in results] and name not in common_excludes:
                    results.append({
                        'title': name,
                        'link': node.get('value', '') or 'N/A',
                        'description': description[:50] if description else 'No description available'
                    })
            
            # Traverse children
            for child in node.get('children', []):
                traverse(child, in_main)
        
        traverse(tree_node)
        return results
    
    def _extract_search_results_from_dom(self, page) -> list:
        """Fallback: Extract search results from DOM."""
        results = []
        
        try:
            # Try different selectors for Google search results
            result_selectors = [
                'div.g',  # Classic result container
                'div[data-sokoban-container]',  # New result format
                'div.MjjYud',  # Another variant
            ]
            
            for selector in result_selectors:
                result_divs = page.locator(selector).all()
                
                if len(result_divs) > 0:
                    for div in result_divs[:7]:
                        try:
                            # Extract title
                            title_elem = div.locator('h3').first
                            title = title_elem.inner_text() if title_elem.count() > 0 else "No title"
                            
                            # Extract link
                            link_elem = div.locator('a').first
                            link = link_elem.get_attribute('href') if link_elem.count() > 0 else "N/A"
                            
                            # Extract description
                            desc_selectors = ['div.VwiC3b', 'div[style*="line-height"]', 'span', 'div']
                            description = "No description available"
                            
                            for desc_sel in desc_selectors:
                                desc_elem = div.locator(desc_sel).first
                                if desc_elem.count() > 0:
                                    desc_text = desc_elem.inner_text()
                                    if desc_text and len(desc_text) > 20:
                                        description = desc_text[:50]
                                        break
                            
                            if title != "No title":
                                results.append({
                                    'title': title,
                                    'link': link,
                                    'description': description
                                })
                                
                        except Exception as e:
                            logger.debug(f"Error extracting result: {e}")
                            continue
                    
                    if results:
                        break
            
        except Exception as e:
            logger.error(f"Error in DOM extraction: {e}")
        
        return results


def create_navigation_tools() -> list[BaseTool]:
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
