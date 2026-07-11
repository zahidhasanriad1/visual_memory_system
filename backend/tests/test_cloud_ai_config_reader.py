import vms_utils.ai.cloud_ai_config_reader as config_reader


def test_get_cloud_ai_settings_reads_gemini_environment(monkeypatch):
    monkeypatch.setenv("USE_GEMINI", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_VISION_MODEL", "gemini-2.0-flash")

    settings = config_reader.get_cloud_ai_settings()

    assert settings.use_gemini is True
    assert settings.gemini_api_key == "test-gemini-key"
    assert settings.gemini_vision_model == "gemini-2.0-flash"


def test_get_cloud_ai_settings_reads_huggingface_environment(monkeypatch):
    monkeypatch.setenv("USE_HUGGINGFACE", "true")
    monkeypatch.setenv("HF_TOKEN", "hf-test-token")
    monkeypatch.setenv(
        "HUGGINGFACE_API_BASE_URL",
        "https://router.huggingface.co/v1/",
    )
    monkeypatch.setenv("HUGGINGFACE_VISION_MODEL", "org/vision-model")
    monkeypatch.setenv("HUGGINGFACE_TEXT_MODEL", "org/text-model")
    monkeypatch.setenv(
        "CLOUD_AI_HYBRID_ORDER",
        "huggingface,unsupported,gemini,openai",
    )

    settings = config_reader.get_cloud_ai_settings()

    assert settings.use_huggingface is True
    assert settings.huggingface_api_key == "hf-test-token"
    assert settings.huggingface_api_base_url == "https://router.huggingface.co/v1"
    assert settings.huggingface_vision_model == "org/vision-model"
    assert settings.huggingface_text_model == "org/text-model"
    assert settings.hybrid_order == ["huggingface", "gemini", "openai"]


def test_get_cloud_ai_settings_normalizes_invalid_default_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "not-a-provider")

    settings = config_reader.get_cloud_ai_settings()

    assert settings.default_provider == "hybrid"
