from pydantic import BaseModel
class DatasetVersionCreateRequestDto(BaseModel):
    name: str
    version: str
    class_names: list[str] = []
