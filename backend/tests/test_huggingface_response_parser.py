from vms_utils.ai.cloud_ai_response_parser import extract_huggingface_output_text


def test_extract_huggingface_output_text_from_string_content() -> None:
    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": '{"summary":"ready"}',
                }
            }
        ]
    }

    assert extract_huggingface_output_text(response) == '{"summary":"ready"}'


def test_extract_huggingface_output_text_from_content_parts() -> None:
    response = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "first"},
                        {"type": "text", "text": "second"},
                    ]
                }
            }
        ]
    }

    assert extract_huggingface_output_text(response) == "first\nsecond"
