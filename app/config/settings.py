# app/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator

from typing import Dict, List, Any, Optional, Union
import os


class Settings(BaseSettings):
    """
    Universal AI Chatbot configuration.

    Environment variables use a DOUBLE underscore (`__`) to indicate nesting:
        LLM_PROVIDER_CONFIGS__OPENAI__ENDPOINT=https://api.openai.com/v1
        OPENAI_API_KEY=sk-xxxxxxxx
    """

    # ──────────────────────────  API  ──────────────────────────
    api_title: str = "Universal AI Chatbot"
    api_version: str = "2.0.0"
    api_description: str = "FastAPI backend with multi-provider LLM support"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_docs_url: str = "/docs"
    api_redoc_url: str = "/redoc"

    # ───────────────  Provider enable list  ───────────────
    llm_providers: List[str] = Field(default=["ollama", "openai", "anthropic", "gemini"])

    # ───────────────  Default generation parameters  ───────────────
    default_llm_provider: str = Field(default="ollama")
    default_llm_model: str = Field(default="llama2")
    default_temperature: float = Field(default=0.7)
    default_max_tokens: int = Field(default=150)

    # ───────────────  Reliability  ───────────────
    enable_fallback: bool = Field(default=True)
    fallback_providers: List[str] = Field(default=["openai", "anthropic", "gemini"])

    @validator("llm_providers", "fallback_providers", pre=True)
    def parse_list_from_env(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v.split(",")
        return v

    @validator("default_llm_provider")
    def _default_provider_in_list(cls, v, values):
        providers = values.get("llm_providers", [])
        if not providers and v == "ollama":  # Allow default if no providers set yet
            return v
        if v not in providers:
            raise ValueError(f"Default provider '{v}' must be in llm_providers")
        return v

    # ───────────────  Provider-specific configs  ───────────────
    llm_provider_configs: Dict[str, Dict[str, Any]] = {
        "ollama": {
            "endpoint": "http://localhost:11434",
            "api_key": "",
            "default_model": "llama2",
            "available_models": ["llama2", "codellama", "mistral"],
            "supports_streaming": True,
            "supports_functions": False,
            "provider_type": "local",
            "timeout": 60,
            "cost_per_1k_tokens": 0.0,
        },
        "openai": {
            "endpoint": "https://api.openai.com/v1",
            "api_key": "",
            "default_model": "gpt-3.5-turbo",
            "available_models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            "supports_streaming": True,
            "supports_functions": True,
            "provider_type": "cloud",
            "timeout": 30,
            "cost_per_1k_tokens": {"gpt-4": 0.03, "gpt-4-turbo": 0.01, "gpt-3.5-turbo": 0.002},
        },
        "anthropic": {
            "endpoint": "https://api.anthropic.com/v1",
            "api_key": "",
            "default_model": "claude-3-sonnet-20240229",
            "available_models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "supports_streaming": True,
            "supports_functions": True,
            "provider_type": "cloud",
            "timeout": 30,
            "cost_per_1k_tokens": {
                "claude-3-opus-20240229": 0.015,
                "claude-3-sonnet-20240229": 0.003,
                "claude-3-haiku-20240307": 0.00025,
            },
        },
        "gemini": {
            "endpoint": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": "",
            "default_model": "gemini-pro",
            "available_models": ["gemini-pro", "gemini-pro-vision"],
            "supports_streaming": True,
            "supports_functions": False,
            "provider_type": "cloud",
            "timeout": 30,
            "cost_per_1k_tokens": {"gemini-pro": 0.0005},
        },
    }

    # ───────────────  Reliability  ───────────────
    enable_fallback: bool = True
    fallback_providers: List[str] = ["openai", "anthropic", "gemini"]
    max_fallback_attempts: int = 3
    provider_timeout: int = 30

    # ───────────────  Cost / usage tracking  ───────────────
    enable_cost_tracking: bool = True
    daily_cost_limit: float = 10.0
    monthly_cost_limit: float = 100.0
    cost_alert_threshold: float = 0.80  # 80 %

    # ───────────────  Rate-limiting  ───────────────
    enable_rate_limiting: bool = True
    requests_per_minute: int = 60
    requests_per_hour: int = 1_000
    burst_limit: int = 10

    # ───────────────  Logging  ───────────────
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_file: Optional[str] = "universal_chatbot.log"
    log_requests: bool = True
    log_responses: bool = False
    log_provider_calls: bool = True

    # ───────────────  Misc  ───────────────
    debug: bool = False
    reload: bool = False

    # Pydantic config
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    # ───────────────  Validators  ───────────────
    @validator("llm_providers")
    def _ensure_providers(cls, v):
        if not v:
            raise ValueError("At least one LLM provider must be enabled")
        return v

    @validator("default_llm_provider")
    def _default_provider_in_list(cls, v, values):
        providers = values.get("llm_providers", [])
        if v not in providers:
            raise ValueError(f"Default provider '{v}' must be in llm_providers")
        return v

    # ───────────────  Init: load env overrides  ───────────────
    def __init__(self, **data):
        super().__init__(**data)
        self._load_env_provider_configs()
        self._validate_provider_configs()

    # Helper: load per-provider env vars
    def _load_env_provider_configs(self):
        for provider in self.llm_providers:
            cfg = self.llm_provider_configs.setdefault(provider, {})
            # Endpoint
            ep_key = f"LLM_PROVIDER_CONFIGS__{provider.upper()}__ENDPOINT"
            if ep_key in os.environ:
                cfg["endpoint"] = os.environ[ep_key]
            # API key: multiple aliases
            for alias in (
                f"LLM_PROVIDER_CONFIGS__{provider.upper()}__API_KEY",
                f"{provider.upper()}_API_KEY",
            ):
                if alias in os.environ and os.environ[alias]:
                    cfg["api_key"] = os.environ[alias]
            # Default model
            dm_key = f"LLM_PROVIDER_CONFIGS__{provider.upper()}__DEFAULT_MODEL"
            if dm_key in os.environ:
                cfg["default_model"] = os.environ[dm_key]

    # Helper: sanity-check configs
    def _validate_provider_configs(self):
        for provider in self.llm_providers:
            cfg = self.llm_provider_configs.get(provider)
            if not cfg:
                raise ValueError(f"Missing configuration for provider '{provider}'")
            if not cfg.get("endpoint"):
                raise ValueError(f"Provider '{provider}' missing endpoint")
            if cfg.get("provider_type") == "cloud" and not cfg.get("api_key"):
                # Warn, but don't block startup
                print(f"⚠️  Warning: no API key set for cloud provider '{provider}'")

    # ───────────────  Public helpers  ───────────────
    def provider_cfg(self, name: str) -> Dict[str, Any]:
        if name not in self.llm_provider_configs:
            raise KeyError(f"Provider '{name}' not configured")
        return self.llm_provider_configs[name]

    def provider_cost(self, name: str, model: Optional[str] = None) -> Union[float, Dict[str, float]]:
        cfg = self.provider_cfg(name)
        cost = cfg.get("cost_per_1k_tokens", 0.0)
        if isinstance(cost, dict) and model:
            return cost.get(model, 0.0)
        return cost


# Singleton settings instance
settings = Settings()


# Convenience aliases
DEFAULT_PROVIDER = settings.default_llm_provider
DEFAULT_MODEL = settings.default_llm_model
ENABLED_PROVIDERS = settings.llm_providers
API_HOST = settings.api_host
API_PORT = settings.api_port
