from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..store.memory import store_context, get_context
from ..events.producer import produce_event
from ..events.schemas import ContextUpdatedEvent
from ..reliability import (
    increment_metric, log_request, log_response, log_error,
    generate_request_id, reliability
)

router = APIRouter()


class ContextPayload(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: dict
    delivered_at: Optional[str] = None


@router.post("/context")
def ingest_context(data: ContextPayload):
    start_time = datetime.now().timestamp()
    request_id = generate_request_id()
    
    increment_metric("total_requests")
    log_request(request_id, "/v1/context", {
        "context_id": data.context_id,
        "scope": data.scope,
        "version": data.version
    })
    
    if data.scope not in ["merchant", "customer", "session"]:
        increment_metric("failed_responses")
        log_error(request_id, "/v1/context", Exception("Invalid scope"))
        raise HTTPException(status_code=400, detail="Invalid scope")
    
    try:
        result = store_context(
            scope=data.scope,
            context_id=data.context_id,
            version=data.version,
            payload=data.payload
        )
        
        # Produce event to Kafka
        merchant_id = data.payload.get("merchant", {}).get("id", "unknown")
        event = ContextUpdatedEvent(
            payload=data.payload,
            context_id=data.context_id,
            merchant_id=merchant_id
        )
        produce_event("context_events", event.to_dict())
        
        increment_metric("successful_responses")
        latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
        log_response(request_id, "/v1/context", "success", latency_ms, "context_stored")
        return result
        
    except Exception as e:
        increment_metric("failed_responses")
        log_error(request_id, "/v1/context", e, str(e.__traceback__))
        raise