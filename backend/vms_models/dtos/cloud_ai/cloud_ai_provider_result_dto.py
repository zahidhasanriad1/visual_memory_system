from typing import Any

from pydantic import BaseModel


class CloudAiProviderResultDto(BaseModel):
    provider: str
    model: str
    agent_name: str
    prompt: str
    output_text: str
    parsed_json: dict[str, Any] | None = None
    raw_response: dict[str, Any] | None = None