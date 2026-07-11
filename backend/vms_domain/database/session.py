from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from vms_api.appsettings import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.app_debug, future=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session


async def create_database_schema() -> None:
    from vms_domain.database.base import Base
    import vms_domain.entities.user_entity  # noqa: F401
    import vms_domain.entities.video_entity  # noqa: F401
    import vms_domain.entities.video_job_entity  # noqa: F401
    import vms_domain.entities.video_frame_entity  # noqa: F401
    import vms_domain.entities.tracked_object_entity  # noqa: F401
    import vms_domain.entities.visual_memory_entity  # noqa: F401
    import vms_domain.entities.adaptive_learning_item_entity  # noqa: F401
    import vms_domain.entities.annotation_project_entity  # noqa: F401
    import vms_domain.entities.annotation_task_entity  # noqa: F401
    import vms_domain.entities.annotation_object_entity  # noqa: F401
    import vms_domain.entities.model_version_entity  # noqa: F401
    import vms_domain.entities.training_job_entity  # noqa: F401
    import vms_domain.entities.dataset_version_entity  # noqa: F401
    import vms_domain.entities.audit_log_entity  # noqa: F401
    import vms_domain.entities.object_identity_entity  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if engine.dialect.name == "sqlite":
            columns = await connection.execute(text("PRAGMA table_info(annotation_objects)"))
            column_names = {str(row[1]) for row in columns.fetchall()}
            if "geometry_type" not in column_names:
                await connection.execute(
                    text(
                        "ALTER TABLE annotation_objects ADD COLUMN "
                        "geometry_type VARCHAR(40) NOT NULL DEFAULT 'box'"
                    )
                )
            if "points" not in column_names:
                await connection.execute(
                    text(
                        "ALTER TABLE annotation_objects ADD COLUMN "
                        "points JSON NOT NULL DEFAULT '[]'"
                    )
                )
