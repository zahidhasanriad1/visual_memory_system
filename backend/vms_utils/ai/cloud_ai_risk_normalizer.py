import copy
import json
from typing import Any

from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto


MARITIME_TERMS = {
    "maritime",
    "ocean",
    "sea",
    "water",
}

VESSEL_TERMS = {
    "boat",
    "cargo ship",
    "ship",
    "tanker",
    "vessel",
}

MARITIME_PROXIMITY_TERMS = {
    "alongside",
    "adjacent",
    "bunkering",
    "close proximity",
    "lightering",
    "multiple ships",
    "multiple vessels",
    "nearby",
    "rendezvous",
    "ship-to-ship",
    "side by side",
    "support vessel",
    "two ships",
    "two vessels",
}


def normalize_image_provider_result(
    agent_name: str,
    provider_result: CloudAiProviderResultDto,
) -> CloudAiProviderResultDto:
    if agent_name not in {"scene_understanding", "safety_review"}:
        return provider_result

    parsed_json = provider_result.parsed_json

    if not isinstance(parsed_json, dict):
        return provider_result

    normalized_json, changed = normalize_image_risk_json(agent_name, parsed_json)

    if not changed:
        return provider_result

    return provider_result.model_copy(
        update={
            "parsed_json": normalized_json,
            "output_text": json.dumps(normalized_json, indent=2),
        }
    )


def normalize_image_risk_json(
    agent_name: str,
    parsed_json: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    normalized_json = copy.deepcopy(parsed_json)
    risk_level = str(normalized_json.get("risk_level", "")).strip().lower()

    if risk_level != "normal":
        return normalized_json, False

    if not _has_maritime_proximity_signal(normalized_json):
        return normalized_json, False

    normalized_json["risk_level"] = "attention"

    if agent_name == "safety_review":
        _normalize_safety_review(normalized_json)
    else:
        _normalize_scene_understanding(normalized_json)

    return normalized_json, True


def _normalize_scene_understanding(parsed_json: dict[str, Any]) -> None:
    parsed_json["reasoning_note"] = (
        "Multiple vessels in close proximity at sea should be flagged for manual "
        "attention, even without visible distress or damage."
    )


def _normalize_safety_review(parsed_json: dict[str, Any]) -> None:
    risk_reasons = parsed_json.get("risk_reasons")

    if not isinstance(risk_reasons, list):
        risk_reasons = []

    reason = "Multiple vessels are in close proximity at sea."

    if reason not in risk_reasons:
        risk_reasons.append(reason)

    parsed_json["risk_reasons"] = risk_reasons
    parsed_json["recommended_review_action"] = "manual_review"

    if not parsed_json.get("summary"):
        parsed_json["summary"] = "Close-proximity maritime activity needs manual review."


def _has_maritime_proximity_signal(parsed_json: dict[str, Any]) -> bool:
    text = " ".join(_flatten_text(parsed_json)).lower()

    has_maritime_context = (
        str(parsed_json.get("environment", "")).strip().lower() == "maritime"
        or any(term in text for term in MARITIME_TERMS)
    )
    has_vessel = any(term in text for term in VESSEL_TERMS)
    has_proximity = any(term in text for term in MARITIME_PROXIMITY_TERMS)

    return has_maritime_context and has_vessel and has_proximity


def _flatten_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        flattened: list[str] = []

        for item in value:
            flattened.extend(_flatten_text(item))

        return flattened

    if isinstance(value, dict):
        flattened = []

        for item in value.values():
            flattened.extend(_flatten_text(item))

        return flattened

    return []
