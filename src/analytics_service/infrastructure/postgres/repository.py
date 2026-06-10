"""Repository for task analytics."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from analytics_service.core.logger import get_logger
from analytics_service.infrastructure.postgres.models import TaskAnalyticsModel
from analytics_service.schemas.events import TaskEventSchema

logger = get_logger(__name__)


class AnalyticsRepository:
    async def save_task_event(
        self, session: AsyncSession, event: TaskEventSchema
    ) -> None:
        payload = event.payload
        
        # Parse datetime fields
        created_at = payload.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = payload.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        raw_assignees = payload.get("metadata", {}).get("assignees")
        
        if isinstance(raw_assignees, list):
            final_assignees = raw_assignees
        elif isinstance(raw_assignees, str) and raw_assignees.strip():
            # Защита от легаси-данных: если вдруг придет строка, делаем из неё список
            final_assignees = [raw_assignees]
        else:
            final_assignees = None

        analytics = TaskAnalyticsModel(
            event_id=event.event_id,
            event_type=event.event_type,
            task_id=payload.get("task_id"),
            title=payload.get("title"),
            description=payload.get("description"),
            status=payload.get("status"),
            user_id=payload.get("user_id"),
            assignees=final_assignees,
            priority=payload.get("metadata", {}).get("priority"),
            created_at=created_at,
            updated_at=updated_at,
        )
        
        session.add(analytics)
        logger.info(f"✅ Saved task event to DB: {event.event_id}, task_id={payload.get('task_id')}")
