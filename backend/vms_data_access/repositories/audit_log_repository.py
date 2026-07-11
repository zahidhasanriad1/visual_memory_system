from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.audit_log_entity import AuditLogEntity

class AuditLogRepository(BaseRepository[AuditLogEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLogEntity)
