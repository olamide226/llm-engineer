from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

from llm_engineer.console import console, SIMPLE

class Config(BaseSettings, extra="allow"):
    """
    Configuration settings for the application.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", protected_namespaces=["settings_"])

    # custom settings for OpenAI compatible endpoints
    custom_refresh_token: str = ""
    custom_api_token: str = ""
    custom_app_key: str = ""
    custom_api_host: str = ""

    open_api_base_url: str = "https://api.openai.com"

    tavily_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    model_provider: str = "custom"
    model_name: str = "gpt-4o"

    @model_validator(mode="after")
    def check_settings(self) -> "Config":
        if self.model_provider == "custom" and (self.custom_api_host == "" or self.custom_api_token == "" or self.custom_refresh_token == ""):
            console.print(SIMPLE, "Custom API host not found in environment variables. Please set the custom API settings to use custom provider.")
            raise SystemExit(1)
        
        if self.model_provider in ("custom", "ollama") and self.open_api_base_url == "":
            console.print(SIMPLE, "OpenAI API base URL not found in environment variables. Please set the OpenAI API base URL to use provider.")
            raise SystemExit(1)
        if self.model_provider not in ["custom", "anthropic", "openai", "ollama"]:
            console.print(SIMPLE, f"Invalid model provider: {self.model_provider}. Please choose from: {model_providers}")
            raise SystemExit(1)

        if self.model_provider == "anthropic" and self.anthropic_api_key == "":
            console.print(SIMPLE, "Anthropic API key not found in environment variables. Please set the Anthropic API key to use Anthropic provider.")
            raise SystemExit(1)
        
        if self.model_provider == "openai" and self.openai_api_key == "":
            console.print(SIMPLE, "OpenAI API key not found in environment variables. Please set the OpenAI API key to use Litellm provider.")
            raise SystemExit(1)
        
        if self.tavily_api_key == "":
            console.print(SIMPLE, "Tavily API key not found in environment variables. Search functionality will be disabled.")
        
        
            
        return self
models = [ "gpt-4o", "gpt-4o-mini", "PS", "claude-3-haiku", "claude-3-5-sonnet", "ollama_chat/llama3.1"]
model_providers = ["PS", "anthropic", "openai", "ollama", "custom"]

config = Config()
