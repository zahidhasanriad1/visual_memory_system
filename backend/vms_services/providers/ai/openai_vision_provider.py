from pathlib import Path

import httpx

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto
from vms_services.interfaces.i_cloud_ai_provider import ICloudAiProvider
from vms_utils.ai.cloud_ai_config_reader import CloudAiSettings
from vms_utils.ai.cloud_ai_file_encoder import encode_image_data_url
from vms_utils.ai.cloud_ai_response_parser import (
    extract_openai_output_text,
    try_parse_json_from_text,
)


class OpenAiVisionProvider(ICloudAiProvider):
    provider_name = "openai"

    def __init__(self, settings: CloudAiSettings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return self.settings.use_openai and bool(self.settings.openai_api_key)

    async def analyze_image(
        self,
        image_path: Path,
        prompt: str,
        agent_name: str,
        detail: str = "auto",
    ) -> CloudAiProviderResultDto:
        if not self.is_configured():
            raise RuntimeError("OpenAI provider is not configured.")

        payload = {
            "model": self.settings.openai_vision_model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                        {
                            "type": "input_image",
                            "image_url": encode_image_data_url(image_path),
                            "detail": detail,
                        },
                    ],
                }
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.openai_api_base_url}/responses",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            response_json = response.json()

        output_text = extract_openai_output_text(response_json)

        return CloudAiProviderResultDto(
            provider=self.provider_name,
            model=self.settings.openai_vision_model,
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
            raise RuntimeError("OpenAI provider is not configured.")

        payload = {
            "model": self.settings.openai_vision_model,
            "input": prompt,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.openai_api_base_url}/responses",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            response_json = response.json()

        output_text = extract_openai_output_text(response_json)

        return CloudAiProviderResultDto(
            provider=self.provider_name,
            model=self.settings.openai_vision_model,
            agent_name=agent_name,
            prompt=prompt,
            output_text=output_text,
            parsed_json=try_parse_json_from_text(output_text),
            raw_response=response_json,
        )