from vms_utils.enums.cloud_ai_agent_enum import CloudAiAgentName


def build_image_prompt(agent_name: CloudAiAgentName, context: str | None = None) -> str:
    context_block = f"\nAdditional project/user context:\n{context}\n" if context else ""

    if agent_name == "scene_understanding":
        return f"""
You are an expert AI vision scene understanding agent for VMS-X: Adaptive Visual Memory Intelligence Platform.

Analyze the uploaded image carefully.
Do not invent objects that are not visible.
Do not replace YOLO/ONNX detection.
Return valid JSON only.
Risk guidance:
- Use "attention" for multiple vessels in close proximity, alongside formations, ship-to-ship transfer, lightering, bunkering, support-vessel activity, or ambiguous maritime operations that need review.
- Do not mark close-proximity maritime activity as "normal" solely because there is no visible distress or damage.
- Use "critical" only for visible collision, fire, sinking, severe damage, distress, or immediate hazard.

Schema:
{{
  "scene_summary": "short visual summary",
  "visible_objects": ["object names"],
  "environment": "aerial | maritime | ground | indoor | outdoor | unknown",
  "supported_detection_classes_seen": ["airplane", "boat", "car", "ship"],
  "semantic_tags": ["tag1", "tag2"],
  "risk_level": "normal | attention | critical | unknown",
  "reasoning_note": "short explanation"
}}
{context_block}
""".strip()

    if agent_name == "object_metadata":
        return f"""
You are an object metadata agent for VMS-X.

Analyze the uploaded image or crop and create semantic metadata for visual memory.
Do not replace detector output.
Return valid JSON only.

Schema:
{{
  "object_caption": "short object-level caption",
  "possible_class": "airplane | boat | car | ship | unknown",
  "visual_attributes": ["color", "shape", "size", "orientation"],
  "semantic_tags": ["tag1", "tag2"],
  "search_keywords": ["keyword1", "keyword2"],
  "confidence_note": "short note"
}}
{context_block}
""".strip()

    if agent_name == "safety_review":
        return f"""
You are a safety review agent for VMS-X.

Analyze the uploaded image for abnormal operational context.
Do not identify people.
Do not make law-enforcement claims.
Return valid JSON only.
Risk guidance:
- Use "attention" for multiple vessels in close proximity, alongside formations, ship-to-ship transfer, lightering, bunkering, support-vessel activity, or ambiguous maritime operations that need review.
- Do not mark close-proximity maritime activity as "normal" solely because there is no visible distress or damage.
- Use "critical" only for visible collision, fire, sinking, severe damage, distress, or immediate hazard.

Schema:
{{
  "risk_level": "normal | attention | critical | unknown",
  "risk_reasons": ["reason1", "reason2"],
  "scene_constraints": ["constraint1", "constraint2"],
  "recommended_review_action": "none | manual_review | urgent_review",
  "summary": "short summary"
}}
{context_block}
""".strip()

    if agent_name == "memory_query":
        return f"""
You are a memory query agent for VMS-X.

Analyze the image and generate useful semantic search terms for visual memory retrieval.
Return valid JSON only.

Schema:
{{
  "query_caption": "short description",
  "search_terms": ["term1", "term2"],
  "likely_classes": ["airplane", "boat", "car", "ship"],
  "semantic_filters": ["filter1", "filter2"]
}}
{context_block}
""".strip()

    return f"""
You are a video timeline summary agent.
For this image/frame input, summarize timeline relevance.
Return valid JSON only.

Schema:
{{
  "summary": "short summary",
  "timeline_relevance": "keyframe | object_frame | background_frame | unknown",
  "semantic_tags": ["tag1", "tag2"]
}}
{context_block}
""".strip()


def build_text_prompt(
    agent_name: CloudAiAgentName,
    report_text: str,
    context: str | None = None,
) -> str:
    context_block = f"\nAdditional context:\n{context}\n" if context else ""

    if agent_name == "video_timeline_summary":
        task = """
You are a video intelligence timeline agent for VMS-X.

Summarize this detection/tracking/timeline report professionally.
Return valid JSON only.

Schema:
{
  "video_summary": "short video summary",
  "main_events": ["event1", "event2"],
  "object_tracks_summary": ["track summary"],
  "class_summary": {},
  "important_timestamps": [],
  "recommended_next_action": "none | manual_review | reprocess_with_higher_accuracy"
}
"""

    elif agent_name == "safety_review":
        task = """
You are a safety review agent for VMS-X.

Review this report and identify operational risk.
Return valid JSON only.

Schema:
{
  "risk_level": "normal | attention | critical | unknown",
  "risk_reasons": ["reason1", "reason2"],
  "recommended_review_action": "none | manual_review | urgent_review",
  "summary": "short summary"
}
"""

    elif agent_name == "memory_query":
        task = """
You are a memory query agent for VMS-X.

Convert this report into searchable memory metadata.
Return valid JSON only.

Schema:
{
  "search_summary": "short searchable summary",
  "search_terms": ["term1", "term2"],
  "semantic_tags": ["tag1", "tag2"],
  "likely_classes": ["airplane", "boat", "car", "ship"]
}
"""

    else:
        task = """
You are a professional AI vision report writer for VMS-X.

Summarize the report clearly.
Return valid JSON only.

Schema:
{
  "summary": "short summary",
  "key_points": ["point1", "point2"],
  "semantic_tags": ["tag1", "tag2"]
}
"""

    return f"""
{task}

Report text:
{report_text}
{context_block}
""".strip()
