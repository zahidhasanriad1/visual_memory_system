from vms_models.dtos.auth.auth_response_dto import AuthResponseDto
from vms_models.dtos.auth.login_request_dto import LoginRequestDto
from vms_models.dtos.auth.register_request_dto import RegisterRequestDto
from vms_models.dtos.auth.user_profile_response_dto import UserProfileResponseDto


class IAuthService:
    async def register(self, request: RegisterRequestDto) -> AuthResponseDto:
        raise NotImplementedError

    async def login(self, request: LoginRequestDto) -> AuthResponseDto:
        raise NotImplementedError

    async def get_current_user(self, token: str) -> UserProfileResponseDto:
        raise NotImplementedError