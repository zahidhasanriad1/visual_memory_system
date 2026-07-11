from pydantic import BaseModel

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto


class CloudAiTextSummaryResultDto(BaseModel):
    provider_result: CloudAiProviderResultDto