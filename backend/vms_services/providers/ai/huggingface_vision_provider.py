import asyncio
from pathlib import Path
from typing import Any

import httpx

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto
from vms_services.interfaces.i_cloud_ai_provider import ICloudAiProvider
from vms_utils.ai.cloud_ai_config_reader import CloudAiSettings
from vms_utils.ai.cloud_ai_file_encoder import encode_image_data_url
from vms_utils.ai.cloud_ai_response_parser import (
    extract_huggingface_output_text,
    try_parse_json_from_text,
)


class HuggingFaceVisionProvider(ICloudAiProvider):
    """Hugging Face Inference Providers client for image and text chat tasks."""

    provider_name = "huggingface"

    def __init__(self, settings: CloudAiSettings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return (
            self.settings.use_huggingface
            and bool(self.settings.huggingface_api_key)
            and bool(self.settings.huggingface_api_base_url)
            and bool(self.settings.huggingface_vision_model)
            and bool(self.settings.huggingface_text_model)
        )

    async def analyze_image(
        self,
        image_path: Path,
        prompt: str,
        agent_name: str,
        detail: str = "auto",
    ) -> CloudAiProviderResultDto:
        del detail  # Hugging Face's chat-completions contract has no detail control.

        if not self.is_configured():
            raise RuntimeError("Hugging Face provider is not configured.")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": encode_image_data_url(image_path),
                        },
                    },
                ],
            }
        ]
        response_json = await self._create_chat_completion(
            model=self.settings.huggingface_vision_model,
            messages=messages,
        )
        output_text = extract_huggingface_output_text(response_json)

        return CloudAiProviderResultDto(
            provider=self.provider_name,
            model=self.settings.huggingface_vision_model,
            agent_name=agent_name,
            prompt=prompt,
            output_text=output_text,
            parsed_json=try_parse_json_from_text(output_text),
            raw_response=response_json,
        )

    async def summarize_text(
        self,
        prompt: str,
        agent_name: str,
    ) -> CloudAiProviderResultDto:
        if not self.is_configured():
            raise RuntimeError("Hugging Face provider is not configured.")

        response_json = await self._create_chat_completion(
            model=self.settings.huggingface_text_model,
            messages=[{"role": "user", "content": prompt}],
        )
        output_text = extract_huggingface_output_text(response_json)

        return CloudAiProviderResultDto(
            provider=self.provider_name,
            model=self.settings.huggingface_text_model,
            agent_name=agent_name,
            prompt=prompt,
            output_text=output_text,
            parsed_json=try_parse_json_from_text(output_text),
            raw_response=response_json,
        )

    async def _create_chat_completion(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.huggingface_api_key}",
            "Content-Type": "application/json",
        }

        max_retries = max(0, self.settings.max_retries)

        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            for attempt in range(max_retries + 1):
                try:
                    response = await client.post(
                        self._chat_completions_url(),
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    break
                except (httpx.TransportError, httpx.HTTPStatusError) as error:
                    if attempt >= max_retries or not self._is_retryable_error(error):
                        raise

                    await asyncio.sleep(min(0.25 * (2**attempt), 2.0))

        if not isinstance(response_json, dict):
            raise RuntimeError("Hugging Face returned an invalid response payload.")

        return response_json

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        if isinstance(error, httpx.TransportError):
            return True

        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            return status_code == 429 or status_code >= 500

        return False

    def _chat_completions_url(self) -> str:
        base_url = self.settings.huggingface_api_base_url.rstrip("/")

        if base_url.endswith("/chat/completions"):
            return base_url

        return f"{base_url}/chat/completions"
