from abc import ABC, abstractmethod

from vms_domain.entities.user_entity import UserEntity


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> UserEntity | None:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> UserEntity | None:
        pass

    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        pass