from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from vms_models.dtos.cloud_ai.cloud_ai_image_analysis_request_dto import CloudAiImageAnalysisRequestDto
from vms_models.dtos.cloud_ai.cloud_ai_text_summary_request_dto import CloudAiTextSummaryRequestDto
from vms_services.interfaces.i_cloud_ai_agent_service import ICloudAiAgentService
from vms_services.service_injection import get_cloud_ai_agent_service
from vms_utils.enums.cloud_ai_agent_enum import CloudAiAgentName
from vms_utils.enums.cloud_ai_provider_enum import CloudAiProviderName

router = APIRouter(prefix="/cloud-ai", tags=["Cloud AI Agents"])


def _public_cloud_data(value):
    if isinstance(value, dict):
        return {
            key: _public_cloud_data(item)
            for key, item in value.items()
            if not key.endswith("_path") and not key.endswith("_paths")
        }
    if isinstance(value, list):
        return [_public_cloud_data(item) for item in value]
    return value


@router.get("/health")
async def cloud_ai_health(
    cloud_ai_service: ICloudAiAgentService = Depends(get_cloud_ai_agent_service),
):
    result = cloud_ai_service.get_health()

    return {
        "success": True,
        "message": "Cloud AI agent service is healthy.",
        "data": result.model_dump(),
    }


@router.get("/agents")
async def list_cloud_ai_agents(
    cloud_ai_service: ICloudAiAgentService = Depends(get_cloud_ai_agent_service),
):
    result = cloud_ai_service.get_agents()

    return {
        "success": True,
        "message": "Cloud AI agents loaded successfully.",
        "data": [agent.model_dump() for agent in result],
    }


@router.post("/connectivity")
async def check_cloud_ai_connectivity(
    cloud_ai_service: ICloudAiAgentService = Depends(get_cloud_ai_agent_service),
):
    result = await cloud_ai_service.check_connectivity()
    return {
        "success": True,
        "message": "Cloud provider connectivity check completed.",
        "data": result,
    }


@router.post("/analyze-image")
async def analyze_image_with_cloud_ai(
    file: UploadFile = File(...),
    provider: CloudAiProviderName = Form("hybrid"),
    agent_name: CloudAiAgentName = Form("scene_understanding"),
    context: str | None = Form(None),
    detail: str = Form("auto"),
    cloud_ai_service: ICloudAiAgentService = Depends(get_cloud_ai_agent_service),
):
    try:
        request = CloudAiImageAnalysisRequestDto(
            provider=provider,
            agent_name=agent_name,
            context=context,
            detail=detail,
        )

        result = await cloud_ai_service.analyze_uploaded_image(
            file=file,
            request=request,
        )

        return {
            "success": True,
            "message": "Cloud AI image analysis completed successfully.",
            "data": _public_cloud_data(result.model_dump()),
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Cloud AI image analysis failed.",
                "reason": str(error),
            },
        ) from error


@router.post("/summarize-report")
async def summarize_report_with_cloud_ai(
    report_text: str = Form(...),
    provider: CloudAiProviderName = Form("hybrid"),
    agent_name: CloudAiAgentName = Form("video_timeline_summary"),
    context: str | None = Form(None),
    cloud_ai_service: ICloudAiAgentService = Depends(get_cloud_ai_agent_service),
):
    try:
        request = CloudAiTextSummaryRequestDto(
            provider=provider,
            agent_name=agent_name,
            report_text=report_text,
            context=context,
        )

        result = await cloud_ai_service.summarize_report(request=request)

        return {
            "success": True,
            "message": "Cloud AI report summary completed successfully.",
            "data": _public_cloud_data(result.model_dump()),
        }

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Cloud AI report summary failed.",
                "reason": str(error),
            },
        ) from error
