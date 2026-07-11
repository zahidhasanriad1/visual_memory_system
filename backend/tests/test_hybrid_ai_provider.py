import asyncio

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import (
    CloudAiProviderResultDto,
)
from vms_services.providers.ai.hybrid_ai_provider import HybridAiProvider
from vms_utils.ai.cloud_ai_config_reader import CloudAiSettings


def _settings() -> CloudAiSettings:
    return CloudAiSettings(
        default_provider="hybrid",
        use_huggingface=True,
        huggingface_api_key="hf-test-token",
        huggingface_api_base_url="https://router.huggingface.co/v1",
        huggingface_vision_model="org/vision-model",
        huggingface_text_model="org/text-model",
        use_openai=False,
        openai_api_key="",
        openai_vision_model="openai-model",
        openai_api_base_url="https://api.openai.com/v1",
        use_gemini=True,
        gemini_api_key="gemini-test-key",
        gemini_vision_model="gemini-model",
        gemini_api_base_url="https://generativelanguage.googleapis.com",
        timeout_seconds=20,
        max_retries=0,
        hybrid_order=["huggingface", "gemini", "openai"],
    )


class _FakeProvider:
    def __init__(self, configured: bool, provider_name: str, should_fail: bool = False):
        self._configured = configured
        self.provider_name = provider_name
        self.should_fail = should_fail

    def is_configured(self) -> bool:
        return self._configured

    async def summarize_text(self, prompt: str, agent_name: str):
        if self.should_fail:
            raise RuntimeError("temporary provider failure")

        return CloudAiProviderResultDto(
            provider=self.provider_name,
            model=f"{self.provider_name}-model",
            agent_name=agent_name,
            prompt=prompt,
            output_text='{"summary":"fallback worked"}',
            parsed_json={"summary": "fallback worked"},
        )


def test_hybrid_health_uses_huggingface_contract() -> None:
    router = HybridAiProvider(_settings())
    router.providers = {
        "huggingface": _FakeProvider(True, "huggingface"),
        "gemini": _FakeProvider(True, "gemini"),
        "openai": _FakeProvider(False, "openai"),
    }

    assert router.get_health() == {
        "default_provider": "hybrid",
        "huggingface_enabled": True,
        "openai_enabled": False,
        "gemini_enabled": True,
        "hybrid_order": ["huggingface", "gemini", "openai"],
    }


def test_hybrid_text_summary_falls_back_in_configured_order() -> None:
    router = HybridAiProvider(_settings())
    router.providers = {
        "huggingface": _FakeProvider(True, "huggingface", should_fail=True),
        "gemini": _FakeProvider(True, "gemini"),
        "openai": _FakeProvider(False, "openai"),
    }

    result = asyncio.run(
        router.summarize_text(
            prompt="Summarize this report",
            agent_name="video_timeline_summary",
        )
    )

    assert result.provider == "gemini"
    assert result.parsed_json == {"summary": "fallback worked"}
