import asyncio
import time
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile, HTTPException

from vms_models.dtos.cloud_ai.cloud_ai_agent_dto import CloudAiAgentDto
from vms_models.dtos.cloud_ai.cloud_ai_health_response_dto import CloudAiHealthResponseDto
from vms_models.dtos.cloud_ai.cloud_ai_image_analysis_request_dto import CloudAiImageAnalysisRequestDto
from vms_models.dtos.cloud_ai.cloud_ai_image_analysis_result_dto import CloudAiImageAnalysisResultDto
from vms_models.dtos.cloud_ai.cloud_ai_text_summary_request_dto import CloudAiTextSummaryRequestDto
from vms_models.dtos.cloud_ai.cloud_ai_text_summary_result_dto import CloudAiTextSummaryResultDto
from vms_services.interfaces.i_cloud_ai_agent_service import ICloudAiAgentService
from vms_services.providers.ai.hybrid_ai_provider import HybridAiProvider
from vms_utils.ai.cloud_ai_config_reader import get_cloud_ai_settings
from vms_utils.ai.cloud_ai_file_encoder import sanitize_filename_stem
from vms_utils.ai.cloud_ai_prompt_builder import build_image_prompt, build_text_prompt
from vms_utils.ai.cloud_ai_risk_normalizer import normalize_image_provider_result


class CloudAiAgentService(ICloudAiAgentService):
    def __init__(self) -> None:
        self.settings = get_cloud_ai_settings()
        self.provider_router = HybridAiProvider(self.settings)

        self.storage_root = Path("storage").resolve()
        self.cloud_ai_upload_dir = self.storage_root / "uploads" / "cloud_ai_images"
        self.cloud_ai_upload_dir.mkdir(parents=True, exist_ok=True)

    def get_health(self) -> CloudAiHealthResponseDto:
        health = self.provider_router.get_health()

        return CloudAiHealthResponseDto(
            status="healthy",
            default_provider=str(health["default_provider"]),
            huggingface_enabled=bool(health["huggingface_enabled"]),
            openai_enabled=bool(health["openai_enabled"]),
            gemini_enabled=bool(health["gemini_enabled"]),
            hybrid_order=list(health["hybrid_order"]),
        )

    def get_agents(self) -> list[CloudAiAgentDto]:
        return [
            CloudAiAgentDto(
                agent_name="scene_understanding",
                display_name="Scene Understanding Agent",
                description="Understands scene context, visible objects, environment, and semantic tags.",
                best_for=[
                    "image scene caption",
                    "video keyframe understanding",
                    "semantic scene analysis",
                ],
            ),
            CloudAiAgentDto(
                agent_name="object_metadata",
                display_name="Object Metadata Agent",
                description="Creates semantic metadata for detected object crops or full images.",
                best_for=[
                    "object caption",
                    "memory metadata enrichment",
                    "search keyword generation",
                ],
            ),
            CloudAiAgentDto(
                agent_name="video_timeline_summary",
                display_name="Video Timeline Summary Agent",
                description="Summarizes detection, tracking, and video timeline reports.",
                best_for=[
                    "video report summary",
                    "track summary",
                    "event understanding",
                ],
            ),
            CloudAiAgentDto(
                agent_name="safety_review",
                display_name="Safety Review Agent",
                description="Reviews scene/report for operational risk and manual review need.",
                best_for=[
                    "risk review",
                    "manual review queue",
                    "attention flags",
                ],
            ),
            CloudAiAgentDto(
                agent_name="memory_query",
                display_name="Memory Query Agent",
                description="Builds semantic search terms for visual memory retrieval.",
                best_for=[
                    "semantic search",
                    "memory query enhancement",
                    "tag extraction",
                ],
            ),
        ]

    async def check_connectivity(self) -> list[dict]:
        async def check(provider_name: str) -> dict:
            provider = self.provider_router.providers[provider_name]
            if not provider.is_configured():
                return {
                    "provider": provider_name,
                    "configured": False,
                    "connected": False,
                    "message": "API key or provider configuration is missing.",
                    "latency_ms": None,
                }
            started = time.perf_counter()
            try:
                await provider.summarize_text(
                    prompt="Reply with API_OK only.",
                    agent_name="connectivity_check",
                )
                return {
                    "provider": provider_name,
                    "configured": True,
                    "connected": True,
                    "message": "Provider authentication and inference are working.",
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                }
            except Exception as error:
                status_code = getattr(getattr(error, "response", None), "status_code", None)
                if status_code in {401, 403}:
                    message = "Authentication or inference permission was rejected."
                elif status_code == 429:
                    message = "Provider quota or rate limit was reached."
                elif error.__class__.__name__ in {"ConnectError", "ConnectTimeout"}:
                    message = "Provider endpoint is unreachable from the backend."
                else:
                    message = f"Provider check failed ({error.__class__.__name__})."
                return {
                    "provider": provider_name,
                    "configured": True,
                    "connected": False,
                    "message": message,
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                }

        return await asyncio.gather(
            check("huggingface"),
            check("gemini"),
            check("openai"),
        )

    async def analyze_uploaded_image(
        self,
        file: UploadFile,
        request: CloudAiImageAnalysisRequestDto,
    ) -> CloudAiImageAnalysisResultDto:
        saved_image_path = await self._save_uploaded_image(file)

        prompt = build_image_prompt(
            agent_name=request.agent_name,
            context=request.context,
        )

        provider = self.provider_router.get_provider(request.provider)

        provider_result = await provider.analyze_image(
            image_path=saved_image_path,
            prompt=prompt,
            agent_name=request.agent_name,
            detail=request.detail,
        )
        provider_result = normalize_image_provider_result(
            agent_name=request.agent_name,
            provider_result=provider_result,
        )

        return CloudAiImageAnalysisResultDto(
            original_filename=file.filename or "uploaded_image",
            saved_image_path=str(saved_image_path.resolve()),
            provider_result=provider_result,
        )

    async def summarize_report(
        self,
        request: CloudAiTextSummaryRequestDto,
    ) -> CloudAiTextSummaryResultDto:
        prompt = build_text_prompt(
            agent_name=request.agent_name,
            report_text=request.report_text,
            context=request.context,
        )

        provider = self.provider_router.get_provider(request.provider)

        provider_result = await provider.summarize_text(
            prompt=prompt,
            agent_name=request.agent_name,
        )

        return CloudAiTextSummaryResultDto(
            provider_result=provider_result,
        )

    async def _save_uploaded_image(self, file: UploadFile) -> Path:
        original_filename = file.filename or "uploaded_image.jpg"
        suffix = Path(original_filename).suffix.lower()

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".webp",
            ".tif",
            ".tiff",
        }

        if suffix not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Unsupported image file extension for Cloud AI analysis.",
                    "filename": original_filename,
                    "supported_extensions": sorted(allowed_extensions),
                },
            )

        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Uploaded image is empty.",
                    "filename": original_filename,
                },
            )

        safe_stem = sanitize_filename_stem(original_filename)
        short_id = uuid4().hex[:8]
        saved_path = self.cloud_ai_upload_dir / f"{safe_stem}_{short_id}_cloud_ai{suffix}"

        saved_path.write_bytes(content)

        return saved_path
