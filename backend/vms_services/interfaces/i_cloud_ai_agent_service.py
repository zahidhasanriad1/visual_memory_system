from abc import ABC, abstractmethod

from fastapi import UploadFile

from vms_models.dtos.cloud_ai.cloud_ai_agent_dto import CloudAiAgentDto
from vms_models.dtos.cloud_ai.cloud_ai_health_response_dto import CloudAiHealthResponseDto
from vms_models.dtos.cloud_ai.cloud_ai_image_analysis_request_dto import CloudAiImageAnalysisRequestDto
from vms_models.dtos.cloud_ai.cloud_ai_image_analysis_result_dto import CloudAiImageAnalysisResultDto
from vms_models.dtos.cloud_ai.cloud_ai_text_summary_request_dto import CloudAiTextSummaryRequestDto
from vms_models.dtos.cloud_ai.cloud_ai_text_summary_result_dto import CloudAiTextSummaryResultDto


class ICloudAiAgentService(ABC):
    @abstractmethod
    def get_health(self) -> CloudAiHealthResponseDto:
        pass

    @abstractmethod
    def get_agents(self) -> list[CloudAiAgentDto]:
        pass

    @abstractmethod
    async def check_connectivity(self) -> list[dict]:
        pass

    @abstractmethod
    async def analyze_uploaded_image(
        self,
        file: UploadFile,
        request: CloudAiImageAnalysisRequestDto,
    ) -> CloudAiImageAnalysisResultDto:
        pass

    @abstractmethod
    async def summarize_report(
        self,
        request: CloudAiTextSummaryRequestDto,
    ) -> CloudAiTextSummaryResultDto:
        pass
