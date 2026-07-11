import base64
import mimetypes
from typing import Any

import httpx

from vms_api.appsettings import get_settings
from vms_utils.ai.cloud_ai_response_parser import (
    extract_huggingface_output_text,
    try_parse_json_from_text,
)


class HuggingFaceVlmClient:
    """Hugging Face VLM client used for lightweight object naming."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def name_object(
        self,
        image_bytes: bytes,
        filename: str | None = None,
    ) -> dict[str, Any]:
        if not self._is_configured():
            return self._unavailable_result("Hugging Face provider is not configured.")

        prompt = (
            "Look only at the main object in this crop. Return valid JSON only. "
            "If confident, provide common object_name. If unsure, use unknown_object "
            "and short_explanation. "
            'Schema: {"object_name":"cow","confidence_level":"high|medium|low",'
            '"confidence_score":1.0,"is_unknown":false,"short_explanation":null}'
        )
        mime_type = mimetypes.guess_type(filename or "")[0] or "image/jpeg"
        image_data_url = (
            f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        )
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url},
                        },
                    ],
                }
            ],
            "stream": False,
            "temperature": 0.1,
            "max_tokens": 512,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.huggingface_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.vlm_timeout_seconds,
            ) as client:
                response = await client.post(
                    self._chat_completions_url(),
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                response_json = response.json()

            if not isinstance(response_json, dict):
                raise RuntimeError("Hugging Face returned an invalid response payload.")

            raw = extract_huggingface_output_text(response_json)
        except Exception as error:
            return self._unavailable_result(str(error))

        data = try_parse_json_from_text(raw)

        if data is None:
            data = {
                "object_name": "unknown_object",
                "confidence_level": "low",
                "confidence_score": 0.0,
                "is_unknown": True,
                "short_explanation": raw[:300],
            }

        data["vlm_status"] = "completed"
        data["vlm_error"] = None

        return data

    @property
    def _model(self) -> str:
        return (
            self._settings.huggingface_vlm_model
            or self._settings.huggingface_vision_model
        )

    def _is_configured(self) -> bool:
        return (
            self._settings.use_huggingface
            and bool(self._settings.huggingface_api_key)
            and bool(self._settings.huggingface_api_base_url)
            and bool(self._model)
        )

    def _chat_completions_url(self) -> str:
        base_url = self._settings.huggingface_api_base_url.rstrip("/")

        if base_url.endswith("/chat/completions"):
            return base_url

        return f"{base_url}/chat/completions"

    @staticmethod
    def _unavailable_result(reason: str) -> dict[str, Any]:
        return {
            "object_name": "unknown_object",
            "confidence_level": "low",
            "confidence_score": 0.0,
            "is_unknown": True,
            "short_explanation": "VLM provider unavailable.",
            "vlm_status": "unavailable",
            "vlm_error": reason,
        }
