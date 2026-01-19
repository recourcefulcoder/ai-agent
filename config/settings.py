from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    default_llm_model: str = "z_ai/z-ai/glm-4.5-air:free"
    
    browser_headless: bool = False
    browser_slow_mo: int = 100
    browser_timeout: int = 30000
    
    max_retries: int = 3  # max agent task retires
    require_confirmation_for_sensitive: bool = True
    
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/agent.log"
    
    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent
    
    @property
    def prompts_dir(self) -> Path:
        """Get the prompts directory."""
        return self.project_root / "config" / "prompts"
    
    def get_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt template from the prompts directory.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            
        Returns:
            The prompt template content
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")


# Global settings instance
settings = Settings()
