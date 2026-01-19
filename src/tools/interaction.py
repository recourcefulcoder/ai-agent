from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from browser.manager import BrowserManager
from browser.locator import ElementLocator
from utils.logger import logger


class ClickInput(BaseModel):
    """Input schema for click_element tool."""
    description: str = Field(
        description="Natural language description of the element to click (e.g., 'Submit button', 'Sign in link')"
    )


class TypeInput(BaseModel):
    """Input schema for type_text tool."""
    text: str = Field(description="The text to type")
    target: Optional[str] = Field(
        default=None,
        description="Description of the input field to type into (if None, types into focused element)"
    )


class ExtractInput(BaseModel):
    """Input schema for extract_text tool."""
    selector: Optional[str] = Field(
        default=None,
        description="CSS selector for specific element (if None, extracts all visible text)"
    )


class ClickElementTool(BaseTool):
    """
    Tool for clicking on page elements.
    """
    
    name: str = "click_element"
    description: str = """
    Click on an element on the page.
    Describe the element in natural language (e.g., "Submit button", "Login link", "Accept cookies").
    The tool will intelligently locate and click the element.
    
    Example: click_element(description="Sign in button")
    """
    args_schema: type[BaseModel] = ClickInput
    browser_manager: BrowserManager = Field(exclude=True)
    
    def _run(self, description: str) -> str:
        """Synchronous version (not used)."""
        raise NotImplementedError("Use async version")
    
    async def _arun(self, description: str) -> str:
        """
        Click on the described element.
        
        Args:
            description: Natural language description of the element
            
        Returns:
            Success or failure message
        """
        logger.info(f"Clicking element: {description}")
        
        # TODO: Get current page from browser manager
        # TODO: Create ElementLocator
        # TODO: Find element using semantic search
        # TODO: Verify element is visible and clickable
        # TODO: Click the element
        # TODO: Wait briefly for any navigation/changes
        # TODO: Return success message
        
        pass


class TypeTextTool(BaseTool):
    """
    Tool for typing text into input fields.
    """
    
    name: str = "type_text"
    description: str = """
    Type text into an input field.
    If target is specified, finds and focuses that field first.
    If target is None, types into the currently focused element.
    
    Example: type_text(text="john@example.com", target="Email input field")
    """
    args_schema: type[BaseModel] = TypeInput
    browser_manager: BrowserManager = Field(exclude=True)
    
    def _run(self, text: str, target: Optional[str] = None) -> str:
        """Synchronous version (not used)."""
        raise NotImplementedError("Use async version")
    
    async def _arun(self, text: str, target: Optional[str] = None) -> str:
        """
        Type text into an input field.
        
        Args:
            text: The text to type
            target: Optional description of the input field
            
        Returns:
            Success message
        """
        logger.info(f"Typing text into: {target or 'focused element'}")
        
        # TODO: Get current page
        # TODO: If target specified, find and click the input field
        # TODO: Clear existing text if any
        # TODO: Type the text with realistic delay
        # TODO: Return success message
        
        pass


class ExtractTextTool(BaseTool):
    """
    Tool for extracting text from the page.
    """
    
    name: str = "extract_text"
    description: str = """
    Extract text content from the page.
    If selector is provided, extracts text from that specific element.
    Otherwise, extracts all visible text from the page.
    
    Example: extract_text(selector=".product-price")
    """
    args_schema: type[BaseModel] = ExtractInput
    browser_manager: BrowserManager = Field(exclude=True)
    
    def _run(self, selector: Optional[str] = None) -> str:
        """Synchronous version (not used)."""
        raise NotImplementedError("Use async version")
    
    async def _arun(self, selector: Optional[str] = None) -> str:
        """
        Extract text from the page.
        
        Args:
            selector: Optional CSS selector for specific element
            
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from: {selector or 'entire page'}")
        
        # TODO: Get current page
        # TODO: If selector provided, find element and get text
        # TODO: Otherwise, get all visible text from page
        # TODO: Clean and format the text
        # TODO: Return extracted text
        
        pass


def create_interaction_tools(browser_manager: BrowserManager) -> list[BaseTool]:
    """
    Create all interaction tools.
    
    Args:
        browser_manager: The browser manager instance
        
    Returns:
        List of interaction tools
    """
    return [
        ClickElementTool(browser_manager=browser_manager),
        TypeTextTool(browser_manager=browser_manager),
        ExtractTextTool(browser_manager=browser_manager),
    ]
