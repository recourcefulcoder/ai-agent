from typing import Optional, List
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from config.settings import settings
from utils.logger import logger


class Singleton(type):
    _instances = set()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class BrowserManager(metaclass=Singleton):
    """
    Manages the lifecycle of a Playwright browser instance.
    Connects to an existing Firefox browser session via CDP (Chrome DevTools Protocol).
    """
    
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._current_page: Optional[Page] = None
        self.start()
    
    def start(self, cdp_url: str = "http://localhost:9222") -> Page:
        """
        Connect to an existing Firefox browser and return the active page.
        
        To start Firefox with remote debugging enabled, use:
        firefox --remote-debugging-port=9222
        
        Or for a specific profile:
        firefox --remote-debugging-port=9222 --profile /path/to/profile
        
        Args:
            cdp_url: The CDP (Chrome DevTools Protocol) endpoint URL.
                     Default is http://localhost:9222
        
        Returns:
            The currently active browser page
            
        Raises:
            Exception: If connection fails or no pages are available
        """
        logger.info(f"Connecting to existing Firefox browser at {cdp_url}...")
        
        try:
            self._playwright = sync_playwright().start()
            logger.debug("Playwright initialized")
            
            self._browser = self._playwright.chromium.connect_over_cdp(cdp_url)
            logger.info("Successfully connected to browser")
            
            contexts = self._browser.contexts
            
            if not contexts:
                logger.warning("No browser contexts found, creating new context")
                self._context = self._browser.new_context(
                    viewport={'width': 1280, 'height': 720}
                )
            else:
                self._context = contexts[0]
                logger.debug(f"Using existing browser context with {len(self._context.pages)} pages")
            
            pages = self._context.pages
            
            if not pages:
                self._current_page = self._context.new_page()
            else:
                self._current_page = pages[-1]
            
            self._current_page.set_default_timeout(settings.browser_timeout)
            
            logger.info(f"Browser connection established. Current URL: {self._current_page.url}")
            
            return self._current_page
            
        except Exception as e:
            logger.error(f"Failed to connect to browser: {e}")
            self._cleanup()
            raise Exception(f"Could not connect to browser at {cdp_url}. "
                          f"Make sure Firefox is running with: firefox --remote-debugging-port=9222") from e
    
    def stop(self) -> None:      
        self._cleanup()
        logger.info("Successfully disconnected from browser")
    
    def _cleanup(self) -> None:
        if self._context:
            try:
                self._context = None
            except Exception as e:
                logger.warning(f"Error releasing context: {e}")
        
        if self._browser:
            try:
                self._browser.close()
                logger.debug("Disconnected from browser")
                self._browser = None
            except Exception as e:
                logger.warning(f"Error disconnecting from browser: {e}")
        
        if self._playwright:
            try:
                self._playwright.stop()
                logger.debug("Playwright stopped")
                self._playwright = None
            except Exception as e:
                logger.warning(f"Error stopping Playwright: {e}")
        
        self._current_page = None
    
    def new_page(self) -> Page:
        if not self._context:
            raise Exception("Browser not connected. Call start() first.")
        
        logger.info("Creating new page...")
        page = self._context.new_page()
        page.set_default_timeout(settings.browser_timeout)
        
        self._current_page = page
        
        logger.info(f"New page created: {page.url}")
        return page
    
    def close_page(self, page: Page) -> None:
        if not page:
            return
        
        logger.info(f"Closing page: {page.url}")
        
        try:
            page.close()
            if self._current_page == page:
                if self._context and self._context.pages:
                    self._current_page = self._context.pages[-1]
                    logger.debug(f"Switched to page: {self._current_page.url}")
                else:
                    self._current_page = None
                    logger.debug("No pages remaining")
                    
        except Exception as e:
            logger.error(f"Error closing page: {e}")
    
    def switch_to_page(self, page_index: int = -1) -> Optional[Page]:
        if not self._context:
            logger.warning("Browser not connected")
            return None
        
        pages = self._context.pages
        
        if not pages:
            logger.warning("No pages available")
            return None
        
        try:
            self._current_page = pages[page_index]
            self._current_page.bring_to_front()
            logger.info(f"Switched to page {page_index}: {self._current_page.url}")
            return self._current_page
        except IndexError:
            logger.error(f"Invalid page index: {page_index}")
            return None
    
    def get_all_pages(self) -> list[Page]:
        if not self._context:
            return []
        
        return self._context.pages
    
    @property
    def current_page(self) -> Optional[Page]:
        return self._current_page
    
    @property
    def current_url(self) -> Optional[str]:
        if self._current_page:
            return self._current_page.url
        return None
    
    @property
    def is_connected(self) -> bool:
        return self._browser is not None and self._current_page is not None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
