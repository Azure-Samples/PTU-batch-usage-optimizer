from pydantic import BaseModel, Field, RootModel
from typing import Dict, Any, List


class EventPayload(BaseModel):
    """Schema for incoming event payload"""
    messages: List[Dict[str, Any]] = Field(
        ...,
        description="List of messages"
    )


class BatchEventPayload(RootModel[List[EventPayload]]):
    """Schema for a batch (list) of event payloads"""
    pass