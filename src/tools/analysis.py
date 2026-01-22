"""
Analysis tools for extracting and analyzing page content.
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from browser.manager import BrowserManager
from utils.logger import logger


class TakeScreenshotInput(BaseModel):
    """Input schema for taking screenshots."""
    pass


class TakeScreenshotTool(BaseTool):
    """
    Tool for taking screenshots of the current page.
    """
    
    name: str = "take_screenshot"
    description: str = """
    Take a screenshot of the current page state.
    Useful for debugging or visual verification of page state.
    
    Example: take_screenshot()
    """
    args_schema: type[BaseModel] = TakeScreenshotInput
    browser_manager: BrowserManager = Field(
        exclude=True,
        default_factory=BrowserManager,
    )
    
    def _run(self) -> str:
        """
        Take a screenshot of the current page.
        
        Returns:
            Path to the screenshot file or error message
        """
        logger.info("Taking screenshot...")
        
        page = self.browser_manager.current_page
        
        if not page:
            return "Error: Browser not connected."
        
        try:
            import os
            from datetime import datetime
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = "screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{screenshots_dir}/screenshot_{timestamp}.png"
            
            # Take screenshot
            page.screenshot(path=filename, full_page=True)
            
            logger.info(f"Screenshot saved to: {filename}")
            return f"Screenshot saved to: {filename}"
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return f"Error taking screenshot: {str(e)}"


def create_analysis_tools() -> list[BaseTool]:
    """
    Create all analysis-related tools.
    
    Returns:
        List of analysis tools
    """
    return [
        TakeScreenshotTool(),
    ]
