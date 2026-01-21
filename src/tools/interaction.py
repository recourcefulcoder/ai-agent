import time
from typing import List, Dict

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

from browser.manager import BrowserManager
from browser.locator import ElementLocator
from config.settings import settings
from utils.logger import logger
from services.tools_cache_manager import get_elements_cache

class ClickElementInput(BaseModel):
    """Input schema for clicking an element."""
    element_selector: str = Field(
        description="The unique selector of the element to click (from the interactive elements list)"
    )


class InputTextInput(BaseModel):
    """Input schema for typing text into an element."""
    element_selector: str = Field(
        description="The unique selector of the element to type into (from the interactive elements list)"
    )
    text: str = Field(
        description="The text to type into the element"
    )


class GetElementContextInput(BaseModel):
    """Input schema for getting element context."""
    element_selector: str = Field(
        description="The unique selector of the element to get context for"
    )


class GetInteractiveElementsInput(BaseModel):
    """Input schema for getting all interactive elements on the page."""
    pass  


class GetInformativeElementsInput(BaseModel):
    pass


class ClickElementTool(BaseTool):
    name: str = "click_element"
    description: str = """
    Click on an interactive element on the page.
    You must first use 'get_interactive_elements' to get the list of elements and their IDs.
    Then use this tool with the element's unique selector value to click it.
    This tool returns update on browser changes, if any occured; it may be opening of new window, or new pop-up window appeared, or any changes on the page itself.
    
    Example: click_element(element_selector="#button_id")
    """
    args_schema: type[BaseModel] = ClickElementInput
    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager,
    )
    
    def _run(self, element_selector: str) -> str:
        """
        Click on the element with the given ID.
        
        Args:
            element_selector: The unqie selector of the element to click
            
        Returns:
            Success or error message
        """        
        page = self.browser_manager.current_page
        
        if not page:
            return "Error: Browser not connected. Use the browser manager to connect first."
        
        cache = get_elements_cache().get_cache(page.url)

        if cache is None or element_selector not in cache.keys():
            return f"Error: Element with selector {element_selector} not found. Use 'get_interactive_elements' first to get the list of elements."
        
        element_info = cache.get(element_selector)
        selector = element_info['selector']
        
        try:
            element = page.locator(selector).first
            
            if element.count() == 0:
                return f"Error: Element with selector '{selector}' not found on the page. The page may have changed."
            
            if not element.is_visible():
                logger.warning(f"Element {element_selector} is not visible, attempting to scroll into view")
                element.scroll_into_view_if_needed()

            page_changes = "Successfully clicked element"  # response prototype, holds changes of the page after action.

            try:
                with page.expect_popup(timeout=1000) as popup_info:
                    element.click()
                popup = popup_info.value
                popup.wait_for_load_state()

                self.browser_manager.current_page = popup
                page_changes += f"\nChange occured: switched to new tab with url {popup.url}"

            except PlaywrightTimeoutError:
                #  occures when no popup window appeared on click within 1sec timespan
                #  meaning that click didn't trigger any popup.
                
                pass
            

            
            #wait for some changes
            time.sleep(0.5)
            
            return f"Successfully clicked: {element_info.get('type')} '{element_info.get('label') or element_info.get('contents', 'element')}'"
            # logger.info(f"Successfully clicked element: {element_info.get('type')} - {element_info.get('contents', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error clicking element {element_selector}: {e}")
            return f"Error clicking element: {str(e)}"


class InputTextTool(BaseTool):
    """
    Tool for typing text into input fields by element ID.
    """
    
    name: str = "input_text"
    description: str = """
    Type text into an input field, textarea, or other text-accepting element.
    You must first use 'get_interactive_elements' to find input fields and their unique selectors.
    
    Example: input_text(element_selector="#input_element", text="john@example.com")
    """
    args_schema: type[BaseModel] = InputTextInput
    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager,
    )
    typing_delay: int = Field(default=50, exclude=True)  # Milliseconds between keystrokes
    
    def _run(self, element_selector: str, text: str) -> str:
        """
        Type text into the element with the given ID.
        
        Args:
            element_selector: The ID of the element to type into
            text: The text to type
            
        Returns:
            Success or error message
        """
        logger.info(f"Typing text into element {element_selector}: '{text[:50]}...'")
        
        page = self.browser_manager.current_page
        
        if not page:
            return "Error: Browser not connected."
        
        cache = get_elements_cache().get_cache(page.url)

        if cache is None or element_selector not in cache.keys():
            return f"Error: Element ID {element_selector} not found. Use 'get_interactive_elements' first."
        
        element_info = cache.get(element_selector)
        selector = element_info['selector']
        
        try:
            # Locate the element
            element = page.locator(selector).first
            
            if element.count() == 0:
                return f"Error: Element not found on the page."
            
            if not element.is_visible():
                element.scroll_into_view_if_needed()
            
            element.click()
            time.sleep(0.2)
            
            element.fill("")
            time.sleep(0.1)
            
            element.type(text, delay=self.typing_delay)
            
            logger.info(f"Successfully typed text into: {element_info.get('type')}")
            
            return f"Successfully typed text into: {element_info.get('label') or element_info.get('type', 'element')}"
            
        except Exception as e:
            logger.error(f"Error typing into element {element_selector}: {e}")
            return f"Error typing text: {str(e)}"


class GetElementContextTool(BaseTool):   
    name: str = "get_element_context"
    description: str = f"""
    Get contextual information about an element by examining its parent elements.
    This helps understand what section of the page the element belongs to.
    Returns information about parent elements up to the first block containing text or {settings.context_request_depth} levels up. 
    If you didn't manage to understand element purpose after calling this method, you may use it once more; if you still fail to understand element purpose consider it to be not valuable for your task.
    
    Example: get_element_context(element_selector=7)
    """
    args_schema: type[BaseModel] = GetElementContextInput
    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager,
    )
    
    def _run(self, element_selector: int) -> str:
        """
        Get contextual information about the element.
        
        Args:
            element_selector: The ID of the element to get context for
            
        Returns:
            Context information as a formatted string
        """
        logger.info(f"Getting context for element {element_selector}")
        
        page = self.browser_manager.current_page
        cache = get_elements_cache().get_cache()
        if not page:
            return "Error: Browser not connected."
        
        if element_selector not in cache.keys():
            return f"Error: Element ID {element_selector} not found."
        
        element_info = cache[element_selector]
        selector = element_info['selector']
        
        try:
            element = page.locator(selector).first
            
            if element.count() == 0:
                return "Error: Element not found on the page."
            
            text_substring_size = 200  # defines how much symbols of context text should 
            # be passed to an agent

            context_info = element.evaluate('''(el) => {
                const context = [];
                let current = el.parentElement;
                let level = 0;
                const maxLevels = 5;
                
                while (current && level < maxLevels) {
                    const text = current.innerText?.trim() || '';
                    const hasText = text.length > 0;
                    
                    context.push({
                        level: level + 1,
                        tagName: current.tagName.toLowerCase(),
                        id: current.id || null,
                        className: current.className || null,
                        text: hasText ? text.substring(0, 300) : null,
                        hasText: hasText
                    });
                    
                    if (hasText) break;
                    
                    current = current.parentElement;
                    level++;
                }
                
                return context;
            }''')
            
            # Format the context information
            result = f"Context for element {element_selector} ({element_info.get('type')}):\n\n"
            result += f"Element: {element_info.get('label') or element_info.get('contents', 'N/A')}\n"
            result += f"Selector: {selector}\n\n"
            result += "Parent hierarchy:\n"
            
            for ctx in context_info:
                result += f"\nLevel {ctx['level']}: <{ctx['tagName']}>"
                if ctx['id']:
                    result += f" id='{ctx['id']}'"
                if ctx['className']:
                    class_str = ctx['className'][:50]
                    result += f" class='{class_str}...'" if len(ctx['className']) > 50 else f" class='{ctx['className']}'"
                if ctx['text']:
                    result += f"\n  Text: {ctx['text'][:text_substring_size]}..."
                if ctx['hasText']:
                    result += "\n  (Stopped: found text-containing block)"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting context for element {element_selector}: {e}")
            return f"Error getting element context: {str(e)}"


class GetInteractiveElementsTool(BaseTool):
    name: str = "get_interactive_elements"
    description: str = """
    Get a list of all interactive elements on the current page.
    Returns information about buttons, links, inputs, and other clickable HTML elements of the page as JSON dictionary, where keys are element's attributes (index, name, value (meaning inside value), etc.), and values are values of those attributes.
    Each element gets a unique ID that can be used with other tools like click_element or input_text.
    
    Use this tool first to understand what elements are available on the page.
    
    Example: get_interactive_elements()
    """
    args_schema: type[BaseModel] = GetInteractiveElementsInput
    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager,
    )
    
    def _run(self) -> str:
        """
        Get all interactive elements on the current page.
        
        Returns:
            Formatted list of interactive elements
        """
        logger.info("Getting interactive elements from current page")
        
        page = self.browser_manager.current_page
        cache_manager = get_elements_cache()
        if not page:
            return "Error: Browser not connected."
        
        try:
            elements = ElementLocator().list_informative_elements(page)
            
            cache_manager.clear_cache()
            new_cache = dict()
            for element in elements:
                new_cache[element['id']] = element
            
            cache_manager.set_cache(new_cache)
            
            if not elements:
                return "No interactive elements found on the page."
            
            result = f"Found {len(elements)} interactive elements:\n\n"
            
            # Group by type for better readability
            by_type: Dict[str, List[Dict]] = dict()
            for elem in elements:
                elem_type = elem.get('type', 'unknown')
                if elem_type not in by_type:
                    by_type[elem_type] = []
                by_type[elem_type].append(elem)
            
            result += str(by_type) + f"\nTotal: {len(elements)} elements available for interaction"
            
            logger.info(f"Cached {len(elements)} elements")
            return result
            
        except Exception as e:
            logger.error(f"Error getting interactive elements: {e}")
            return f"Error getting interactive elements: {str(e)}"


class GetInformativeElementsTool(BaseTool):
    name: str = "get_interactive_elements"
    description: str = """
    Get a list of all informative elements on the current page.
    Informative elements are all those elements that contain text information, vital for understanding page contents.
    
    Use this tool to understand the page contents.

    Use cases examples: 
       * you want to scan through film rating site, to find best one
       * you want to find vacancy description on LinkedIn to form best fitting CV for it.
       * you want to make some sort of research, and page contains vital information on the theme being researched.
    
    Example of usage: get_interactive_elements()
    """
    args_schema: type[BaseModel] = GetInteractiveElementsInput
    browser_manager: BrowserManager = Field(
        exclude=True, 
        default_factory=BrowserManager,
    )

    def _arun(self) -> str:
        pass
    
    def _run(self) -> str:
        """
        Get all informative elements (i.e. containing some text 
        information, vital for understanding page contents) on the current page.
        
        Returns:
            Formatted list of interactive elements
        """
        logger.info("Getting interactive elements from current page")
        
        page = self.browser_manager.current_page
        cache_manager = get_elements_cache()
        if not page:
            return "Error: Browser not connected."
        
        try:

            locator = ElementLocator()
            elements = locator.list_interactive_elements(page)
            
            cache_manager.clear_cache()
            new_cache = dict()
            for element in elements:
                new_cache[element['id']] = element
            
            cache_manager.set_cache(new_cache)
            
            if not elements:
                return "No interactive elements found on the page."
            
            result = f"Found {len(elements)} interactive elements:\n\n"
            
            # Group by type for better readability
            by_type: Dict[str, List[Dict]] = dict()
            for elem in elements:
                elem_type = elem.get('type', 'unknown')
                if elem_type not in by_type:
                    by_type[elem_type] = []
                by_type[elem_type].append(elem)
            
            result += str(by_type) + f"\nTotal: {len(elements)} elements available for interaction"
            
            logger.info(f"Cached {len(elements)} elements")
            return result
            
        except Exception as e:
            logger.error(f"Error getting interactive elements: {e}")
            return f"Error getting interactive elements: {str(e)}"


def create_interaction_tools() -> list[BaseTool]:
    """
    Create all interaction tools.
    
    Args:
        browser_manager: The browser manager instance
        
    Returns:
        List of interaction tools
    """
    return [
        ClickElementTool(),
        InputTextTool(),
        GetElementContextTool(),
        GetInteractiveElementsTool(),
    ]
