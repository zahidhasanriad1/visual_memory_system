from pydantic import BaseModel

from vms_utils.enums.cloud_ai_agent_enum import CloudAiAgentName
from vms_utils.enums.cloud_ai_provider_enum import CloudAiProviderName


class CloudAiTextSummaryRequestDto(BaseModel):
    provider: CloudAiProviderName = "hybrid"
    agent_name: CloudAiAgentName = "video_timeline_summary"
    report_text: str
    context: str | None = None