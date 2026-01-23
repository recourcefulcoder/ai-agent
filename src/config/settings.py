from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    default_llm_model: str = "z-ai/glm-4.5-air:free"
    
    browser_headless: bool = False
    browser_slow_mo: int = 100
    browser_timeout: int = 30000
    
    max_retries: int = 3  # max agent task retires
    context_request_depth: int = 5  # defines how deep into 
    # parent blocks can agent go, requesting additional context on an element.
    # max_task_steps: Optional[int] = None
    require_confirmation_for_sensitive: bool = True
    
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/agent.log"
    
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent
    
    @property
    def prompts_dir(self) -> Path:
        return self.project_root / "config" / "prompts"
    
    def get_prompt(self, prompt_name: str) -> str:
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")


settings = Settings()
