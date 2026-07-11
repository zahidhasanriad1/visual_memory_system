from pydantic import BaseModel

from vms_utils.enums.cloud_ai_agent_enum import CloudAiAgentName


class CloudAiAgentDto(BaseModel):
    agent_name: CloudAiAgentName
    display_name: str
    description: str
    best_for: list[str]