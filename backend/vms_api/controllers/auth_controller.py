from fastapi import APIRouter, Depends, Form, Header, HTTPException

from vms_models.dtos.auth.login_request_dto import LoginRequestDto
from vms_models.dtos.auth.register_request_dto import RegisterRequestDto
from vms_services.interfaces.i_auth_service import IAuthService
from vms_services.service_injection import get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(
    request: RegisterRequestDto,
    auth_service: IAuthService = Depends(get_auth_service),
):
    result = await auth_service.register(request)

    return {
        "success": True,
        "message": "Registration completed successfully.",
        "data": result.model_dump(),
    }


@router.post("/login/form")
async def login_form(
    username: str = Form(...),
    password: str = Form(...),
    auth_service: IAuthService = Depends(get_auth_service),
):
    request = LoginRequestDto(
        email=username,
        password=password,
    )

    result = await auth_service.login(request)

    return {
        "success": True,
        "message": "Login completed successfully.",
        "data": result.model_dump(),
    }


@router.post("/logout")
async def logout():
    return {
        "success": True,
        "message": "Logout completed successfully.",
        "data": None,
    }


@router.get("/me")
async def get_me(
    authorization: str | None = Header(default=None),
    auth_service: IAuthService = Depends(get_auth_service),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "message": "Authorization bearer token is missing.",
            },
        )

    token = authorization.split(" ", 1)[1].strip()
    result = await auth_service.get_current_user(token)

    return {
        "success": True,
        "message": "Current user loaded successfully.",
        "data": result.model_dump(),
    }
