from pydantic import BaseModel

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto


class CloudAiImageAnalysisResultDto(BaseModel):
    original_filename: str
    saved_image_path: str
    provider_result: CloudAiProviderResultDto