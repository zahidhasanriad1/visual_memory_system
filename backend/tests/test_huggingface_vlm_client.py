import asyncio
from types import SimpleNamespace
from typing import Any

import vms_utils.ai.huggingface_vlm_client as client_module
from vms_utils.ai.huggingface_vlm_client import HuggingFaceVlmClient


def _settings(**overrides):
    values = {
        "use_huggingface": True,
        "huggingface_api_key": "hf-test-token",
        "huggingface_api_base_url": "https://router.huggingface.co/v1",
        "huggingface_vision_model": "org/vision-model",
        "huggingface_vlm_model": None,
        "vlm_timeout_seconds": 15,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def test_name_object_uses_vision_model_fallback(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    payload = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"object_name":"ship","confidence_level":"high",'
                        '"confidence_score":0.95,"is_unknown":false,'
                        '"short_explanation":null}'
                    )
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
            return _FakeResponse(payload)

    monkeypatch.setattr(client_module, "get_settings", _settings)
    monkeypatch.setattr(client_module.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(HuggingFaceVlmClient().name_object(b"png", "crop.png"))

    assert captured["json"]["model"] == "org/vision-model"
    assert captured["json"]["max_tokens"] == 512
    image_url = captured["json"]["messages"][0]["content"][1]["image_url"]["url"]
    assert image_url.startswith("data:image/png;base64,")
    assert result["object_name"] == "ship"
    assert result["vlm_status"] == "completed"
    assert result["vlm_error"] is None


def test_name_object_preserves_soft_failure_when_provider_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: _settings(huggingface_api_key=""),
    )

    result = asyncio.run(HuggingFaceVlmClient().name_object(b"image", "crop.jpg"))

    assert result == {
        "object_name": "unknown_object",
        "confidence_level": "low",
        "confidence_score": 0.0,
        "is_unknown": True,
        "short_explanation": "VLM provider unavailable.",
        "vlm_status": "unavailable",
        "vlm_error": "Hugging Face provider is not configured.",
    }
