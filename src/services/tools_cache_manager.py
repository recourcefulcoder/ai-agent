# src/services/elements_cache.py
from typing import Dict, Any, Optional


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
        if not hasattr(self, '_cache'):
            self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get_cache(self) -> Dict[str, Dict[str, Any]]:
        return self._cache
    
    def set_cache(self, cache: Dict[str, Dict[str, Any]]) -> None:
        self._cache = cache
    
    def clear_cache(self) -> None:
        self._cache.clear()
    
    def get_element(self, element_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(element_id)


def get_elements_cache() -> ElementsCacheManager:
    return ElementsCacheManager()
