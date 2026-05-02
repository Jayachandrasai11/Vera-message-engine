import json
from ..events.schemas import ContextUpdatedEvent, parse_event, EventType
from ..store.memory import store_context
from ..reliability import log_error


def process_context_event(data: dict) -> dict:
    """Process CONTEXT_UPDATED events."""
    try:
        event = parse_event(data) if "type" in data else ContextUpdatedEvent(
            payload=data.get("payload", {}),
            context_id=data.get("context_id"),
            merchant_id=data.get("merchant_id")
        )
        
        payload = event.payload
        result = store_context(
            scope=payload.get("scope", "merchant"),
            context_id=event.context_id,
            version=payload.get("version", 1),
            payload=payload.get("data", {})
        )
        
        return {
            "status": "success",
            "event_id": event.event_id,
            "result": result
        }
    except Exception as e:
        log_error("context_worker", "process", e, str(e.__traceback__))
        return {
            "status": "error",
            "event_id": data.get("event_id"),
            "error": str(e)
        }


async def run_context_worker(max_retries: int = 3):
    """Run context worker (conceptual - would use Kafka consumer in production)."""
    pass