from dataclasses import dataclass


@dataclass
class UserEntity:
    user_id: str
    full_name: str
    email: str
    password_hash: str
    role: str
    is_active: bool
    created_at: str