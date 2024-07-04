from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class Event(BaseModel):
    event_id: UUID
    request_id: UUID
    session_id: UUID
    user_id: UUID
    user_ts: datetime
    server_ts: datetime
    eventbus_ts: datetime
    url: HttpUrl
    event_type: str
    event_subtype: str | None
    payload: Optional[dict[str, Any]]
