from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from playwright.sync_api import Page

from browser.locator import ElementLocator


@dataclass
class PageCache:
    interactive_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    informative_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    info_updates: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    interactive_updates: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    #  page cache is basicaly dictionary of element selector mapped to info about this element

    def clear_cache(self) -> None:
        self.interactive_cache.clear()


class ElementsCacheManager:
    """
    Singleton manager for page elements cache.
    Persists across tool invocations within a session.
    All the methods, related to working with cache directly (get/set/clear cache) implying interactive cache; informative cache is stored only for update pushes.
    """
    _instance: Optional['ElementsCacheManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._cache_mapping: Dict[str, PageCache] = dict()
        # _cache_mapping maps page url to its interactive_cache; PageCache's "interactive_cache" value is a Dictionary where keys are element's selectors, and values - information about them.

    def get_cache(self, page_url: str) -> List[Dict[str, Any]]:
        page_cache = self._cache_mapping.get(page_url, None)
        if page_cache is None:
            return None 
        return page_cache.interactive_cache
    
    def set_interactive_cache(
        self, 
        page_url: str, 
        interactive_cache: Dict[str, Dict[str, Any]]
    ) -> None:
        if self._cache_mapping.get(page_url, None) is None:
            self._cache_mapping[page_url] = PageCache()
        self.del_interactve_updates(page_url)
        self._cache_mapping[page_url].interactive_cache = interactive_cache
    
    def set_informative_cache(
        self, 
        page_url: str, 
        informative_cache: Dict[str, Dict[str, Any]]
    ) -> None:
        if self._cache_mapping.get(page_url, None) is None:
            self._cache_mapping[page_url] = PageCache()
        self.del_info_updates(page_url)
        self._cache_mapping[page_url].informative_cache = informative_cache
    
    def clear_interactive_cache(self, page_url: str) -> None:
        self._cache_mapping.get(
            page_url, 
            PageCache(),
        ).interactive_cache.clear()

    def clear_informative_cache(self, page_url: str) -> None:
        self._cache_mapping.get(
            page_url, 
            PageCache(),
        ).informative_cache.clear()
    
    def get_element(self, page_url: str, element_selector: str) -> Optional[Dict[str, Any]]:
        return self._cache_mapping.get(
            page_url, 
            PageCache(),
        ).interactive_cache.get(element_selector, None)
    
    def get_info_updates(self, page_url: str) -> Dict[str, Dict[str, Any]]:
        """
        Returns updates of interactive elements on page with specified url
        """
        return self._cache_mapping.get(page_url).info_updates

    def get_interactive_updates(self, page_url: str) -> Dict[str, Dict[str, Any]]:
        """
        Returns updates of interactive elements on page with specified url
        """
        return self._cache_mapping.get(page_url).interactive_updates

    def track_dom_changes(self, page: Page) -> None:
        # page value implied to be valid
        if self._cache_mapping.get(page.url, None) is None:
            self._cache_mapping[page.url] = PageCache()

        info_cache = ElementLocator().list_informative_elements(page)
        inter_cache = ElementLocator().list_interactive_elements(page)

        delta_info = set(info_cache.values()).difference(
            set(self._cache_mapping.get(page.url).informative_cache.values())
        )
        delta_inter = set(inter_cache.values()).difference(
            set(self._cache_mapping.get(page.url).interactive_cache.values())
        )

        if len(delta_info) != 0:
            self._cache_mapping.get(page.url).informative_cache = info_cache 
            for element in delta_info:
                self._cache_mapping.get(page.url).info_updates[element["selector"]] = element
        if len(delta_inter) != 0:
            self._cache_mapping.get(page.url).interactive_cache = inter_cache
            for element in delta_inter:
                self._cache_mapping.get(page.url).interactive_updates[element["selector"]] = element

    def del_info_updates(self, page_url: str):
        self._cache_mapping.get(page_url, PageCache()).informative_updates.clear()

    def del_interactve_updates(self, page_url: str):
        self._cache_mapping.get(page_url, PageCache()).interactive_updates.clear()

    def del_page_updates(self, page_url: str):
        self.del_info_updates(page_url)
        self.del_interactve_updates(page_url)

