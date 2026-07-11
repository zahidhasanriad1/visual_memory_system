import json
import re
from typing import Any


def try_parse_json_from_text(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()

    try:
        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)

    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))

        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None

    return None


def extract_openai_output_text(response_json: dict[str, Any]) -> str:
    direct_text = response_json.get("output_text")

    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    collected: list[str] = []

    for output_item in response_json.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")

            if isinstance(text, str):
                collected.append(text)

            nested_text = content_item.get("output_text")

            if isinstance(nested_text, str):
                collected.append(nested_text)

    return "\n".join(collected).strip()


def extract_gemini_output_text(response_json: dict[str, Any]) -> str:
    collected: list[str] = []

    for candidate in response_json.get("candidates", []):
        content = candidate.get("content", {})

        for part in content.get("parts", []):
            text = part.get("text")

            if isinstance(text, str):
                collected.append(text)

    return "\n".join(collected).strip()


def extract_huggingface_output_text(response_json: dict[str, Any]) -> str:
    """Extract text from Hugging Face's OpenAI-compatible chat response."""

    choices = response_json.get("choices", [])

    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message", {})

    if not isinstance(message, dict):
        return ""

    content = message.get("content")

    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    collected: list[str] = []

    for content_item in content:
        if isinstance(content_item, str):
            collected.append(content_item)
            continue

        if not isinstance(content_item, dict):
            continue

        text = content_item.get("text")

        if isinstance(text, str):
            collected.append(text)

    return "\n".join(collected).strip()
