import time
from concurrent.futures import ThreadPoolExecutor

import vms_services.service_injection as service_injection
import vms_services.services.image_feature_service as image_feature_module


def test_service_provider_starts_without_constructing_feature_services() -> None:
    provider = service_injection.ServiceProvider(session=object())

    assert provider._video_memory is None
    assert provider._adaptive_learning is None
    assert provider._annotation is None
    assert provider._model_registry is None
    assert provider._training is None


def test_image_feature_singleton_is_safe_during_concurrent_cold_start(
    monkeypatch,
) -> None:
    construction_count = 0

    class FakeImageFeatureService:
        def __init__(self) -> None:
            nonlocal construction_count
            time.sleep(0.02)
            construction_count += 1

    monkeypatch.setattr(
        image_feature_module,
        "ImageFeatureService",
        FakeImageFeatureService,
    )
    monkeypatch.setattr(
        service_injection,
        "_image_feature_service_singleton",
        None,
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        instances = list(
            executor.map(
                lambda _: service_injection.get_image_feature_service(),
                range(16),
            )
        )

    assert construction_count == 1
    assert all(instance is instances[0] for instance in instances)
