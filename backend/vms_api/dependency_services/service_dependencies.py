from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from vms_domain.database.session import get_db_session
from vms_services.service_injection import ServiceProvider

async def get_service_provider(session: Annotated[AsyncSession, Depends(get_db_session)]) -> ServiceProvider:
    return ServiceProvider(session)
