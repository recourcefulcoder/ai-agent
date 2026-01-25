from typing import Optional
from langchain_deepseek import ChatDeepSeek
from langchain.chat_models import init_chat_model
from config.settings import settings
from utils.logger import logger


class LLMService:
    def __init__(self):
        self._main_llm: Optional[ChatDeepSeek] = None
    
    def get_main_llm(self) -> ChatDeepSeek:
        if self._main_llm is None:
            logger.info(f"Initializing main LLM: {settings.default_llm_model}")
            self._main_llm = ChatDeepSeek(
                model=settings.default_llm_model,
                base_url=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key,
            )
        
        return self._main_llm


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
