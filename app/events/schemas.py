import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum


class EventType(str, Enum):
    CONTEXT_UPDATED = "CONTEXT_UPDATED"
    TRIGGER_RECEIVED = "TRIGGER_RECEIVED"
    USER_REPLY_RECEIVED = "USER_REPLY_RECEIVED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    MESSAGE_GENERATED = "MESSAGE_GENERATED"


class BaseEvent:
    def __init__(self, event_type: EventType, payload: Dict[str, Any], context_id: str = None, merchant_id: str = None):
        self.event_id = f"evt_{uuid.uuid4().hex[:12]}"
        self.type = event_type
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.context_id = context_id
        self.merchant_id = merchant_id
        self.payload = payload
        self.retry_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type,
            "timestamp": self.timestamp,
            "context_id": self.context_id,
            "merchant_id": self.merchant_id,
            "payload": self.payload,
            "retry_count": self.retry_count
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ContextUpdatedEvent(BaseEvent):
    def __init__(self, payload: Dict[str, Any], context_id: str, merchant_id: str = None):
        super().__init__(EventType.CONTEXT_UPDATED, payload, context_id, merchant_id)


class TriggerReceivedEvent(BaseEvent):
    def __init__(self, payload: Dict[str, Any], context_id: str, merchant_id: str):
        super().__init__(EventType.TRIGGER_RECEIVED, payload, context_id, merchant_id)


class UserReplyReceivedEvent(BaseEvent):
    def __init__(self, payload: Dict[str, Any], context_id: str, merchant_id: str = None):
        super().__init__(EventType.USER_REPLY_RECEIVED, payload, context_id, merchant_id)


class ActionExecutedEvent(BaseEvent):
    def __init__(self, payload: Dict[str, Any], context_id: str, merchant_id: str):
        super().__init__(EventType.ACTION_EXECUTED, payload, context_id, merchant_id)


def parse_event(data: Dict[str, Any]) -> BaseEvent:
    """Parse event from Kafka message."""
    event_type = EventType(data.get("type"))
    payload = data.get("payload", {})
    context_id = data.get("context_id")
    merchant_id = data.get("merchant_id")
    
    event_classes = {
        EventType.CONTEXT_UPDATED: ContextUpdatedEvent,
        EventType.TRIGGER_RECEIVED: TriggerReceivedEvent,
        EventType.USER_REPLY_RECEIVED: UserReplyReceivedEvent,
        EventType.ACTION_EXECUTED: ActionExecutedEvent,
    }
    
    cls = event_classes.get(event_type, BaseEvent)
    event = cls(payload, context_id, merchant_id)
    event.event_id = data.get("event_id", event.event_id)
    event.retry_count = data.get("retry_count", 0)
    return event