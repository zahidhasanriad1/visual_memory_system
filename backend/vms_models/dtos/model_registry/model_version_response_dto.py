from pydantic import BaseModel
class ModelVersionResponseDto(BaseModel):
    id: str
    model_name: str
    model_type: str
    version: str
    model_path: str
    onnx_path: str | None
    class_names: list[str]
    metrics: dict
    status: str
