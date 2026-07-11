from pydantic import BaseModel
class TrainingJobResponseDto(BaseModel):
    job_id: str
    detector_model: str
    status: str
    progress_percent: float
    message: str
    metrics: dict
    output_model_path: str | None = None
