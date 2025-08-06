from typing import Dict
from app.providers.base_provider import BaseLLMProvider
from app.config.settings import settings
import logging
import importlib

logger = logging.getLogger(__name__)

class ProviderFactory:
    """Factory class to create and manage LLM provider instances."""

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._provider_classes = {}
        self._load_enabled_providers()

    def _load_enabled_providers(self):
        for provider in settings.llm_providers:
            try:
                module = importlib.import_module(f"app.providers.{provider}_provider")
                provider_class = getattr(module, f"{provider.capitalize()}Provider")
                self._provider_classes[provider] = provider_class
                logger.info(f"Loaded provider module: {provider}")
            except ImportError as e:
                logger.warning(f"Could not load provider module {provider}: {e}")
            except AttributeError as e:
                logger.warning(f"Could not find provider class for {provider}: {e}")

    async def get_provider(self, provider_name: str) -> BaseLLMProvider:
        if provider_name in self._providers:
            return self._providers[provider_name]
        if provider_name not in settings.llm_provider_configs:
            raise ValueError(f"Provider {provider_name} not configured")
        config = settings.llm_provider_configs[provider_name]
        provider_class = self._provider_classes.get(provider_name)
        if not provider_class:
            raise ValueError(f"Provider {provider_name} not implemented or not enabled")
        instance = provider_class(
            endpoint=config["endpoint"],
            api_key=config["api_key"],
            **config.get("extra_params", {})
        )
        self._providers[provider_name] = instance
        logger.info(f"Created provider instance: {provider_name}")
        return instance

    async def close_all_providers(self):
        for provider in self._providers.values():
            if hasattr(provider, "close"):
                await provider.close()
        self._providers.clear()
