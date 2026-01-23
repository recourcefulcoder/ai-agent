from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from config.settings import settings
from utils.logger import logger


class LLMService:
    def __init__(self):
        self._main_llm: Optional[ChatOpenAI] = None
    
    def get_main_llm(self) -> ChatOpenAI:
        if self._main_llm is None:
            logger.info(f"Initializing main LLM: {settings.default_llm_model}")
            
            # self._main_llm = ChatOpenAI(
            #     base_url=settings.openrouter_base_url,
            #     api_key=settings.openrouter_api_key,
            #     model=settings.default_llm_model,
            #     temperature=0.7,
            # )

            self._main_llm = init_chat_model(
                model=settings.default_llm_model,
                model_provider="openai",
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
            )
        
        return self._main_llm


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
