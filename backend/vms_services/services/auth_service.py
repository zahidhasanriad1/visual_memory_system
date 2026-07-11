from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from vms_data_access.interfaces.i_user_repository import IUserRepository
from vms_domain.entities.user_entity import UserEntity
from vms_models.dtos.auth.auth_response_dto import AuthResponseDto
from vms_models.dtos.auth.login_request_dto import LoginRequestDto
from vms_models.dtos.auth.register_request_dto import RegisterRequestDto
from vms_models.dtos.auth.user_profile_response_dto import UserProfileResponseDto
from vms_services.interfaces.i_auth_service import IAuthService
from vms_utils.security.jwt_token_service import JwtTokenService
from vms_utils.security.password_hasher import PasswordHasher


class AuthService(IAuthService):
    def __init__(
        self,
        user_repository: IUserRepository,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = PasswordHasher()
        self.jwt_token_service = JwtTokenService()

    async def register(self, request: RegisterRequestDto) -> AuthResponseDto:
        email = request.email.strip().lower()

        existing_user = await self.user_repository.get_by_email(email)

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "An account with this email already exists.",
                },
            )

        user = UserEntity(
            user_id=str(uuid4()),
            full_name=request.full_name.strip(),
            email=email,
            password_hash=self.password_hasher.hash_password(request.password),
            role=request.role,
            is_active=True,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        created_user = await self.user_repository.create(user)

        return self._build_auth_response(created_user)

    async def login(self, request: LoginRequestDto) -> AuthResponseDto:
        email = request.email.strip().lower()

        user = await self.user_repository.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Invalid email or password.",
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "This account is disabled.",
                },
            )

        password_valid = self.password_hasher.verify_password(
            request.password,
            user.password_hash,
        )

        if not password_valid:
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Invalid email or password.",
                },
            )

        return self._build_auth_response(user)

    async def get_current_user(self, token: str) -> UserProfileResponseDto:
        try:
            payload = self.jwt_token_service.verify_access_token(token)
        except Exception:
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Invalid or expired token.",
                },
            )

        user_id = str(payload.get("sub", ""))

        user = await self.user_repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "User not found.",
                },
            )

        return UserProfileResponseDto(
            user_id=user.user_id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        )

    def _build_auth_response(self, user: UserEntity) -> AuthResponseDto:
        access_token = self.jwt_token_service.create_access_token(
            {
                "sub": user.user_id,
                "email": user.email,
                "role": user.role,
            }
        )

        return AuthResponseDto(
            access_token=access_token,
            user_id=user.user_id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
        )
