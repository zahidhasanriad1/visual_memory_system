import os
from dataclasses import dataclass
from pathlib import Path


def _get_dotenv_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def _load_dotenv_if_present() -> None:
    dotenv_path = _get_dotenv_path()
    if dotenv_path.exists():
        with dotenv_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)


_load_dotenv_if_present()


@dataclass(frozen=True)
class CloudAiSettings:
    default_provider: str

    use_huggingface: bool
    huggingface_api_key: str
    huggingface_api_base_url: str
    huggingface_vision_model: str
    huggingface_text_model: str

    use_openai: bool
    openai_api_key: str
    openai_vision_model: str
    openai_api_base_url: str

    use_gemini: bool
    gemini_api_key: str
    gemini_vision_model: str
    gemini_api_base_url: str

    timeout_seconds: int
    max_retries: int
    hybrid_order: list[str]


def get_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_cloud_ai_settings() -> CloudAiSettings:
    default_provider = os.getenv("AI_PROVIDER", "hybrid").strip().lower()

    if default_provider not in {"huggingface", "gemini", "openai", "hybrid"}:
        default_provider = "hybrid"

    hybrid_order_text = os.getenv(
        "CLOUD_AI_HYBRID_ORDER",
        "huggingface,gemini,openai",
    )

    hybrid_order = [
        item.strip().lower()
        for item in hybrid_order_text.split(",")
        if item.strip().lower() in {"huggingface", "gemini", "openai"}
    ]

    return CloudAiSettings(
        default_provider=default_provider,
        use_huggingface=get_env_bool("USE_HUGGINGFACE", True),
        huggingface_api_key=os.getenv("HF_TOKEN", "").strip(),
        huggingface_api_base_url=os.getenv(
            "HUGGINGFACE_API_BASE_URL",
            "https://router.huggingface.co/v1",
        ).rstrip("/"),
        huggingface_vision_model=os.getenv(
            "HUGGINGFACE_VISION_MODEL",
            "zai-org/GLM-4.5V:zai-org",
        ).strip(),
        huggingface_text_model=os.getenv(
            "HUGGINGFACE_TEXT_MODEL",
            "Qwen/Qwen2.5-7B-Instruct",
        ).strip(),
        use_openai=get_env_bool("USE_OPENAI", False),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_vision_model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.5").strip(),
        openai_api_base_url=os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        use_gemini=get_env_bool("USE_GEMINI", False),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_vision_model=os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash").strip(),
        gemini_api_base_url=os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/"),
        timeout_seconds=get_env_int("CLOUD_AI_TIMEOUT_SECONDS", 60),
        max_retries=get_env_int("CLOUD_AI_MAX_RETRIES", 2),
        hybrid_order=hybrid_order or ["huggingface", "gemini", "openai"],
    )
