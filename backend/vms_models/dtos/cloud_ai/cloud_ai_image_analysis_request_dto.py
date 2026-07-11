from pydantic import BaseModel, Field

from vms_utils.enums.cloud_ai_agent_enum import CloudAiAgentName
from vms_utils.enums.cloud_ai_provider_enum import CloudAiProviderName


class CloudAiImageAnalysisRequestDto(BaseModel):
    provider: CloudAiProviderName = "hybrid"
    agent_name: CloudAiAgentName = "scene_understanding"
    context: str | None = None
    detail: str = Field(default="auto")