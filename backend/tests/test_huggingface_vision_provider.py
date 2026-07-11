import asyncio
from pathlib import Path
from typing import Any

import vms_services.providers.ai.huggingface_vision_provider as provider_module
from vms_services.providers.ai.huggingface_vision_provider import (
    HuggingFaceVisionProvider,
)
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
        use_gemini=False,
        gemini_api_key="",
        gemini_vision_model="gemini-model",
        gemini_api_base_url="https://generativelanguage.googleapis.com",
        timeout_seconds=20,
        max_retries=0,
        hybrid_order=["huggingface", "gemini", "openai"],
    )


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def test_analyze_image_uses_huggingface_chat_completions(monkeypatch, tmp_path) -> None:
    captured: dict[str, Any] = {}
    response_payload = {
        "choices": [
            {
                "message": {
                    "content": '{"scene_summary":"harbor","risk_level":"normal"}'
                }
            }
        ]
    }

    class FakeAsyncClient:
        def __init__(self, timeout: int) -> None:
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url: str, headers: dict, json: dict) -> _FakeResponse:
            captured.update(url=url, headers=headers, json=json)
            return _FakeResponse(response_payload)

    monkeypatch.setattr(provider_module.httpx, "AsyncClient", FakeAsyncClient)
    image_path = Path(tmp_path) / "sample.png"
    image_path.write_bytes(b"image-bytes")

    result = asyncio.run(
        HuggingFaceVisionProvider(_settings()).analyze_image(
            image_path=image_path,
            prompt="Analyze this image",
            agent_name="scene_understanding",
        )
    )

    assert captured["url"] == "https://router.huggingface.co/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer hf-test-token"
    assert captured["json"]["model"] == "org/vision-model"
    assert captured["json"]["max_tokens"] == 1024
    content = captured["json"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "Analyze this image"}
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert result.provider == "huggingface"
    assert result.model == "org/vision-model"
    assert result.parsed_json == {
        "scene_summary": "harbor",
        "risk_level": "normal",
    }


def test_huggingface_provider_requires_token() -> None:
    settings = _settings()
    settings = CloudAiSettings(
        **{
            **settings.__dict__,
            "huggingface_api_key": "",
        }
    )

    assert HuggingFaceVisionProvider(settings).is_configured() is False
