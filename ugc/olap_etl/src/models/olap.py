from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class OlapSchema(BaseModel):
    id: UUID
    event_id: UUID
    request_id: UUID
    session_id: UUID
    user_id: UUID
    event_time: datetime
    user_ts: datetime
    server_ts: datetime
    eventbus_ts: datetime
    url: HttpUrl
    event_type: str
    event_subtype: Optional[str]
    payload: Optional[dict]
