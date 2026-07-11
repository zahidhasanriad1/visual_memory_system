from abc import ABC, abstractmethod
from pathlib import Path

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto


class ICloudAiProvider(ABC):
    provider_name: str

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image_path: Path,
        prompt: str,
        agent_name: str,
        detail: str = "auto",
    ) -> CloudAiProviderResultDto:
        pass

    @abstractmethod
    async def summarize_text(
        self,
        prompt: str,
        agent_name: str,
    ) -> CloudAiProviderResultDto:
        pass