from pydantic import BaseModel
class ModelRegisterRequestDto(BaseModel):
    model_name: str
    model_type: str
    version: str
    model_path: str
    onnx_path: str | None = None
    class_names: list[str] = []
    metrics: dict = {}
