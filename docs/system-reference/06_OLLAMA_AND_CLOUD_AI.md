# Ollama And Cloud AI

## A. Ollama Local Pipeline

Status: MISSING.

No active `ollama_vlm_client.py`, Ollama settings, route, service dependency, or provider was found in source. A stale `__pycache__/ollama_vlm_client` file exists, but bytecode cache is not executable source evidence.

## B. Hugging Face Provider

Files:

- `backend/vms_services/providers/ai/huggingface_vision_provider.py`
- `backend/vms_utils/ai/cloud_ai_config_reader.py`

Configuration:

- `USE_HUGGINGFACE`, default true
- `HF_TOKEN`
- `HUGGINGFACE_API_BASE_URL`, default `https://router.huggingface.co/v1`
- `HUGGINGFACE_VISION_MODEL`, default `zai-org/GLM-4.5V:zai-org`
- `HUGGINGFACE_TEXT_MODEL`, default `Qwen/Qwen2.5-7B-Instruct`

Request construction:

- Uses chat-completions payload with `messages`.
- Image input is base64 data URL under `image_url.url`.
- Sends `Authorization: Bearer <API_KEY>`.
- Temperature 0.2, `max_tokens=1024`, `stream=false`.
- Retries transport errors, 429, and 5xx up to `CLOUD_AI_MAX_RETRIES`.

Status: IMPLEMENTED BUT NOT PROVIDER-VERIFIED.

## C. Gemini Provider

File: `backend/vms_services/providers/ai/gemini_vision_provider.py`.

Configuration:

- `USE_GEMINI`, default false
- `GEMINI_API_KEY`
- `GEMINI_VISION_MODEL`, default `gemini-2.5-flash`
- `GEMINI_API_BASE_URL`, default `https://generativelanguage.googleapis.com`

Request construction:

- Calls `/v1beta/models/{model}:generateContent`.
- API key is query param `key`.
- Image input uses `inline_data` with guessed MIME and base64 bytes.
- Text summary uses text-only `parts`.
- No explicit retry loop in provider.

Status: IMPLEMENTED BUT NOT PROVIDER-VERIFIED.

## D. OpenAI Provider

File: `backend/vms_services/providers/ai/openai_vision_provider.py`.

Configuration:

- `USE_OPENAI`, default false
- `OPENAI_API_KEY`
- `OPENAI_VISION_MODEL`, default `gpt-5.5`
- `OPENAI_API_BASE_URL`, default `https://api.openai.com/v1`

Actual API used:

- OpenAI Responses API path: `{OPENAI_API_BASE_URL}/responses`.
- Image input uses `input_image` with base64 data URL and `detail`.
- Text summary sends `input: prompt`.
- No explicit retry loop in provider.

Status: IMPLEMENTED BUT NOT PROVIDER-VERIFIED.

## E. Hybrid Provider Router

File: `backend/vms_services/providers/ai/hybrid_ai_provider.py`.

- `AI_PROVIDER` default `hybrid`.
- `CLOUD_AI_HYBRID_ORDER` default `huggingface,gemini,openai`.
- Unsupported provider names raise runtime errors.
- Hybrid skips unconfigured providers and aggregates provider errors.
- It tries providers in order and returns the first successful result.

Status: IMPLEMENTED BUT NOT PROVIDER-VERIFIED.

## F. AI Agents

Agent enum values are implemented in `cloud_ai_agent_enum.py` and returned by `CloudAiAgentService.get_agents()`:

| Agent | Purpose | Input | Prompt builder | Provider | Response |
|---|---|---|---|---|---|
| `scene_understanding` | scene context, objects, environment, semantic tags | image | `build_image_prompt` | selected/hybrid | `CloudAiProviderResultDto` |
| `object_metadata` | metadata for object crops/full images | image | `build_image_prompt` | selected/hybrid | `CloudAiProviderResultDto` |
| `video_timeline_summary` | summarize reports | text report | `build_text_prompt` | selected/hybrid | `CloudAiProviderResultDto` |
| `safety_review` | operational risk/manual review | image or report | prompt builder | selected/hybrid | normalized risk JSON if parseable |
| `memory_query` | semantic search terms/tag extraction | image or report | prompt builder | selected/hybrid | provider result |

Error behavior:

- `analyze-image` wraps non-HTTP exceptions in HTTP 502 with `detail.message` and `detail.reason`.
- `summarize-report` wraps exceptions in HTTP 502.
- Connectivity reports configured/connected/latency without throwing for provider failures.

Security note: 502 `reason` may expose provider exception text. Secrets were not printed in this audit, but production should sanitize provider exception bodies.
