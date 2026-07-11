from pydantic import BaseModel


class CloudAiHealthResponseDto(BaseModel):
    status: str
    default_provider: str
    huggingface_enabled: bool
    openai_enabled: bool
    gemini_enabled: bool
    hybrid_order: list[str]
