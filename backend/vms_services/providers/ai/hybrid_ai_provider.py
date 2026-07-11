from pathlib import Path

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto
from vms_services.providers.ai.gemini_vision_provider import GeminiVisionProvider
from vms_services.providers.ai.huggingface_vision_provider import HuggingFaceVisionProvider
from vms_services.providers.ai.openai_vision_provider import OpenAiVisionProvider
from vms_utils.ai.cloud_ai_config_reader import CloudAiSettings


class HybridAiProvider:
    provider_name = "hybrid"

    def __init__(self, settings: CloudAiSettings) -> None:
        self.settings = settings
        self.providers = {
            "huggingface": HuggingFaceVisionProvider(settings),
            "gemini": GeminiVisionProvider(settings),
            "openai": OpenAiVisionProvider(settings),
        }

    def get_provider(self, provider_name: str):
        normalized = provider_name.strip().lower()

        if normalized == "hybrid":
            return self

        provider = self.providers.get(normalized)

        if provider is None:
            raise RuntimeError(f"Unsupported AI provider: {provider_name}")

        return provider

    def get_health(self) -> dict:
        return {
            "default_provider": self.settings.default_provider,
            "huggingface_enabled": self.providers["huggingface"].is_configured(),
            "openai_enabled": self.providers["openai"].is_configured(),
            "gemini_enabled": self.providers["gemini"].is_configured(),
            "hybrid_order": self.settings.hybrid_order,
        }

    async def analyze_image(
        self,
        image_path: Path,
        prompt: str,
        agent_name: str,
        detail: str = "auto",
    ) -> CloudAiProviderResultDto:
        errors: list[str] = []

        for provider_name in self.settings.hybrid_order:
            provider = self.providers[provider_name]

            if not provider.is_configured():
                errors.append(f"{provider_name}: not configured")
                continue

            try:
                return await provider.analyze_image(
                    image_path=image_path,
                    prompt=prompt,
                    agent_name=agent_name,
                    detail=detail,
                )
            except Exception as error:
                errors.append(f"{provider_name}: {error}")

        raise RuntimeError("All hybrid AI providers failed. " + " | ".join(errors))

    async def summarize_text(
        self,
        prompt: str,
        agent_name: str,
    ) -> CloudAiProviderResultDto:
        errors: list[str] = []

        for provider_name in self.settings.hybrid_order:
            provider = self.providers[provider_name]

            if not provider.is_configured():
                errors.append(f"{provider_name}: not configured")
                continue

            try:
                return await provider.summarize_text(
                    prompt=prompt,
                    agent_name=agent_name,
                )
            except Exception as error:
                errors.append(f"{provider_name}: {error}")

        raise RuntimeError("All hybrid AI providers failed. " + " | ".join(errors))
