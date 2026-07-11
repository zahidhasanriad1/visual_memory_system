import json
from pathlib import Path

from vms_data_access.interfaces.i_user_repository import IUserRepository
from vms_domain.entities.user_entity import UserEntity
from vms_api.appsettings import get_settings


class UserRepository(IUserRepository):
    """
    File-backed user repository.
    Keeps controller/service independent from storage implementation.
    Later this can be replaced with PostgreSQL repository without changing AuthService.
    """

    def __init__(self) -> None:
        self.auth_dir = get_settings().storage_root / "auth"
        self.auth_dir.mkdir(parents=True, exist_ok=True)

        self.users_file = self.auth_dir / "users.json"

        if not self.users_file.exists():
            self.users_file.write_text("[]", encoding="utf-8")

    async def get_by_email(self, email: str) -> UserEntity | None:
        email_normalized = email.strip().lower()

        for item in self._load_users():
            if item["email"].lower() == email_normalized:
                return self._to_entity(item)

        return None

    async def get_by_id(self, user_id: str) -> UserEntity | None:
        for item in self._load_users():
            if item["user_id"] == user_id:
                return self._to_entity(item)

        return None

    async def create(self, user: UserEntity) -> UserEntity:
        users = self._load_users()
        users.append(user.__dict__)
        self._save_users(users)

        return user

    def _load_users(self) -> list[dict]:
        try:
            data = json.loads(self.users_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_users(self, users: list[dict]) -> None:
        self.users_file.write_text(
            json.dumps(users, indent=2),
            encoding="utf-8",
        )

    def _to_entity(self, item: dict) -> UserEntity:
        return UserEntity(
            user_id=item["user_id"],
            full_name=item["full_name"],
            email=item["email"],
            password_hash=item["password_hash"],
            role=item.get("role", "user"),
            is_active=bool(item.get("is_active", True)),
            created_at=item["created_at"],
        )
