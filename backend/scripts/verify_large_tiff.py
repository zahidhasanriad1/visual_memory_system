"""Run a real large-TIFF detection smoke test without exposing filesystem paths."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from fastapi import UploadFile
from starlette.datastructures import Headers

from vms_api.controllers.image_feature_controller import _public_image_data
from vms_services.services.image_feature_service import ImageFeatureService


def _contains_private_path_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).endswith(("_path", "_paths"))
            or _contains_private_path_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_private_path_key(item) for item in value)
    return False


async def _run(image_path: Path, detector: str) -> None:
    service = ImageFeatureService()
    started = time.perf_counter()
    with image_path.open("rb") as stream:
        upload = UploadFile(
            file=stream,
            filename=image_path.name,
            headers=Headers({"content-type": "image/tiff"}),
        )
        result = await service.test_detections(
            upload,
            confidence_threshold=0.25,
            iou_threshold=0.45,
            detector_model=detector,
        )

    data = _public_image_data(result.model_dump())
    print(
        json.dumps(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 2),
                "detector_model": data["detector_model"],
                "source_size": [data["source_width"], data["source_height"]],
                "inference_size": [data["width"], data["height"]],
                "inference_scaled": data["inference_scaled"],
                "detections": data["total_detection_count"],
                "source_image_url": data["source_image_url"],
                "has_private_path_key": _contains_private_path_key(data),
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--detector", choices=("yolo", "skydet"), default="skydet")
    args = parser.parse_args()
    asyncio.run(_run(args.image.resolve(), args.detector))


if __name__ == "__main__":
    main()
