from pydantic import BaseModel


class UserProfileResponseDto(BaseModel):
    user_id: str
    full_name: str
    email: str
    role: str
    is_active: bool