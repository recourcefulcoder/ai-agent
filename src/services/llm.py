"""
LLM service integration with OpenRouter.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from config.settings import settings
from utils.logger import logger


class LLMService:
    """
    Service for interacting with LLMs via OpenRouter.
    """
    
    def __init__(self):
        self._main_llm: Optional[ChatOpenAI] = None
        self._vision_llm: Optional[ChatOpenAI] = None
    
    def get_main_llm(self) -> ChatOpenAI:
        """
        Get the main LLM for planning and reasoning.
        
        Returns:
            ChatOpenAI instance
        """
        if self._main_llm is None:
            logger.info(f"Initializing main LLM: {settings.default_llm_model}")
            
            # TODO: Create ChatOpenAI instance with:
            # - base_url: settings.openrouter_base_url
            # - api_key: settings.openrouter_api_key
            # - model: settings.default_llm_model
            # - temperature: 0.7 (configurable)
            
            self._main_llm = ChatOpenAI(
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key,
                model=settings.default_llm_model,
                temperature=0.7,
            )
        
        return self._main_llm
    
    def get_vision_llm(self) -> ChatOpenAI:
        """
        Get the vision-capable LLM for screenshot analysis.
        
        Returns:
            ChatOpenAI instance with vision support
        """
        if self._vision_llm is None:
            logger.info(f"Initializing vision LLM: {settings.vision_llm_model}")
            
            self._vision_llm = ChatOpenAI(
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key,
                model=settings.vision_llm_model,
                temperature=0.5,
            )
        
        return self._vision_llm


# Global service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get or create the LLM service singleton.
    
    Returns:
        LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
