from vms_models.dtos.cloud_ai.cloud_ai_provider_result_dto import CloudAiProviderResultDto
from vms_utils.ai.cloud_ai_risk_normalizer import (
    normalize_image_provider_result,
    normalize_image_risk_json,
)


def test_scene_understanding_close_proximity_ships_are_attention() -> None:
    parsed_json = {
        "scene_summary": (
            "An aerial view depicting two large ships, one significantly larger "
            "than the other, positioned in close proximity on the open water."
        ),
        "visible_objects": ["ship", "water"],
        "environment": "maritime",
        "supported_detection_classes_seen": ["ship"],
        "semantic_tags": [
            "aerial view",
            "vessel",
            "tanker",
            "cargo ship",
            "ocean",
            "sea",
            "maritime transport",
            "helipad",
        ],
        "risk_level": "normal",
        "reasoning_note": (
            "There are no visible signs of distress, damage, or unusual activity. "
            "The proximity could be routine lightering, bunkering, or support vessel activity."
        ),
    }

    normalized_json, changed = normalize_image_risk_json(
        "scene_understanding",
        parsed_json,
    )

    assert changed is True
    assert normalized_json["risk_level"] == "attention"
    assert "manual attention" in normalized_json["reasoning_note"]


def test_non_proximity_maritime_scene_stays_normal() -> None:
    parsed_json = {
        "scene_summary": "A single ship underway on open water.",
        "visible_objects": ["ship", "water"],
        "environment": "maritime",
        "risk_level": "normal",
    }

    normalized_json, changed = normalize_image_risk_json(
        "scene_understanding",
        parsed_json,
    )

    assert changed is False
    assert normalized_json["risk_level"] == "normal"


def test_provider_output_text_matches_normalized_json() -> None:
    provider_result = CloudAiProviderResultDto(
        provider="gemini",
        model="gemini-test",
        agent_name="scene_understanding",
        prompt="prompt",
        output_text='{"risk_level": "normal"}',
        parsed_json={
            "scene_summary": "Two vessels are in close proximity at sea.",
            "visible_objects": ["ship"],
            "environment": "maritime",
            "risk_level": "normal",
        },
        raw_response={},
    )

    normalized_result = normalize_image_provider_result(
        "scene_understanding",
        provider_result,
    )

    assert normalized_result.parsed_json is not None
    assert normalized_result.parsed_json["risk_level"] == "attention"
    assert '"risk_level": "attention"' in normalized_result.output_text
