from pathlib import Path

import httpx

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto
from vms_services.interfaces.i_cloud_ai_provider import ICloudAiProvider
from vms_utils.ai.cloud_ai_config_reader import CloudAiSettings
from vms_utils.ai.cloud_ai_file_encoder import encode_file_base64, guess_mime_type
from vms_utils.ai.cloud_ai_response_parser import (
    extract_gemini_output_text,
    try_parse_json_from_text,
)


class GeminiVisionProvider(ICloudAiProvider):
    provider_name = "gemini"

    def __init__(self, settings: CloudAiSettings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return self.settings.use_gemini and bool(self.settings.gemini_api_key)

    async def analyze_image(
        self,
        image_path: Path,
        prompt: str,
        agent_name: str,
        detail: str = "auto",
    ) -> CloudAiProviderResultDto:
        if not self.is_configured():
            raise RuntimeError("Gemini provider is not configured.")

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": guess_mime_type(image_path),
                                "data": encode_file_base64(image_path),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
            },
        }

        url = f"{self.settings.gemini_api_base_url}/v1beta/models/{self.settings.gemini_vision_model}:generateContent"

        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                url,
                params={"key": self.settings.gemini_api_key},
                json=payload,
            )
            response.raise_for_status()
            response_json = response.json()

        output_text = extract_gemini_output_text(response_json)

        return CloudAiProviderResultDto(
            provider=self.provider_name,
            model=self.settings.gemini_vision_model,
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
            raise RuntimeError("Gemini provider is not configured.")

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
            },
        }

        url = f"{self.settings.gemini_api_base_url}/v1beta/models/{self.settings.gemini_vision_model}:generateContent"

        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                url,
                params={"key": self.settings.gemini_api_key},
                json=payload,
            )
            response.raise_for_status()
            response_json = response.json()

        output_text = extract_gemini_output_text(response_json)

        return CloudAiProviderResultDto(
            provider=self.provider_name,
            model=self.settings.gemini_vision_model,
            agent_name=agent_name,
            prompt=prompt,
            output_text=output_text,
            parsed_json=try_parse_json_from_text(output_text),
            raw_response=response_json,
        )