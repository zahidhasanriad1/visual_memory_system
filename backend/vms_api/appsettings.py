from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORAGE_ROOT = BACKEND_ROOT / "storage"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{(DEFAULT_STORAGE_ROOT / 'database' / 'vmsx.db').as_posix()}"


class AppSettings(BaseSettings):
    """Central application settings loaded from environment and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="VMS-X Adaptive Visual Memory Intelligence Platform", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    database_url: str = Field(default=DEFAULT_DATABASE_URL, alias="DATABASE_URL")
    jwt_secret_key: str = Field(default="change-this-secret-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=120, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    cors_allowed_origins: str = Field(default="http://localhost:4200,http://127.0.0.1:4200", alias="CORS_ALLOWED_ORIGINS")
    max_upload_size_mb: int = Field(default=1024, alias="MAX_UPLOAD_SIZE_MB")

    storage_root: Path = Field(default=DEFAULT_STORAGE_ROOT, alias="STORAGE_ROOT")
    host_storage_root: str = Field(default="", alias="VMS_HOST_STORAGE_ROOT")
    yolo_model_path: Path = Field(
        default=DEFAULT_STORAGE_ROOT / "models" / "skysealand_yolo12m_best.onnx",
        alias="YOLO_MODEL_PATH",
    )
    skydet_model_path: Path = Field(
        default=DEFAULT_STORAGE_ROOT / "models" / "skydet_skysealand_best.pt",
        alias="SKYDET_MODEL_PATH",
    )

    use_huggingface: bool = Field(default=True, alias="USE_HUGGINGFACE")
    huggingface_api_key: str = Field(default="", alias="HF_TOKEN")
    huggingface_api_base_url: str = Field(
        default="https://router.huggingface.co/v1",
        alias="HUGGINGFACE_API_BASE_URL",
    )
    huggingface_vision_model: str = Field(
        default="zai-org/GLM-4.5V:zai-org",
        alias="HUGGINGFACE_VISION_MODEL",
    )
    huggingface_text_model: str = Field(
        default="Qwen/Qwen2.5-7B-Instruct",
        alias="HUGGINGFACE_TEXT_MODEL",
    )
    huggingface_vlm_model: str | None = Field(
        default=None,
        alias="HUGGINGFACE_VLM_MODEL",
    )
    vlm_timeout_seconds: int = Field(default=120, alias="VLM_TIMEOUT_SECONDS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def upload_dir(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def frame_dir(self) -> Path:
        return self.storage_root / "frames"

    @property
    def crop_dir(self) -> Path:
        return self.storage_root / "crops"

    @property
    def output_dir(self) -> Path:
        return self.storage_root / "outputs"

    @property
    def dataset_dir(self) -> Path:
        return self.storage_root / "datasets"

    @property
    def model_dir(self) -> Path:
        return self.storage_root / "models"

    @property
    def log_dir(self) -> Path:
        return self.storage_root / "logs"

    def ensure_storage_directories(self) -> None:
        required = [
            self.upload_dir,
            self.frame_dir,
            self.crop_dir,
            self.output_dir / "video_memory_videos",
            self.output_dir / "video_memory_reports",
            self.output_dir / "video_memory_tracked_frames",
            self.output_dir / "detection_reports",
            self.dataset_dir / "adaptive_learning",
            self.dataset_dir / "annotations",
            self.dataset_dir / "exports",
            self.model_dir,
            self.log_dir,
            self.storage_root / "database",
        ]
        for directory in required:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.ensure_storage_directories()
    return settings
