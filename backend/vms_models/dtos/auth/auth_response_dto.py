from pydantic import BaseModel


class AuthResponseDto(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    email: str
    role: str