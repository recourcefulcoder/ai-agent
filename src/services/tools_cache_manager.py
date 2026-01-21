from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class PageCache:
    url: str
    cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def clear_cache(self) -> None:
        self.cache.clear()


class ElementsCacheManager:
    """
    Singleton manager for interactive elements cache.
    Persists across tool invocations within a session.
    """
    _instance: Optional['ElementsCacheManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance
    
    def __init__(self):
        if hasattr(self._initialized):
            return
        self._initialized = True
        self._cache_mapping: Dict[str, Dict[str, Dict[str, Any]]] = dict()
        # _cache_mapping maps page url to its cache; page cache is a Dictionary where keys are element's selectors, and values - information about them.

    def get_cache(self, page_url: str) -> Dict[str, Dict[str, Any]]:
        return self._cache_mapping.get(page_url, None)
    
    def set_cache(self, page_url: str, cache: Dict[str, Dict[str, Any]]) -> None:
        self._cache_mapping[page_url] = cache
    
    def clear_cache(self, page_url: str) -> None:
        self._cache_mapping.get(page_url, dict()).clear()
    
    def get_element(self, page_url: str, element_id: str) -> Optional[Dict[str, Any]]:
        return self._cache_mapping.get(page_url, dict()).get(element_id, None)


def get_elements_cache() -> ElementsCacheManager:
    return ElementsCacheManager()
