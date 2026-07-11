from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequestDto(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Literal["admin", "annotator", "user", "viewer"] = "user"
