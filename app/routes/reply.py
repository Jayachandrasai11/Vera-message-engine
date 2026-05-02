from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from ..store.memory import get_context, update_user_status, update_conversation_state
from ..engine.reply import handle_reply, interpret_reply
from ..events.producer import produce_event
from ..events.schemas import UserReplyReceivedEvent
from ..reliability import (
    increment_metric, log_request, log_response, log_error,
    generate_request_id, reliability
)

router = APIRouter()


class ReplyRequest(BaseModel):
    context_id: str
    reply: str


@router.post("/reply")
def reply(request: ReplyRequest):
    start_time = datetime.now().timestamp()
    request_id = generate_request_id()
    
    increment_metric("total_requests")
    log_request(request_id, "/v1/reply", {
        "context_id": request.context_id,
        "reply_preview": request.reply[:50] if len(request.reply) > 50 else request.reply
    })
    
    stored = get_context(request.context_id)
    if not stored:
        increment_metric("failed_responses")
        log_error(request_id, "/v1/reply", Exception("Context not found"))
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "error",
            "rationale": "System could not process request safely"
        }

    merchant_id = stored.get("payload", {}).get("merchant", {}).get("id", "unknown")
    last_action = stored.get("last_action", "unknown")
    last_interaction = stored.get("interactions", [{}])[-1] if stored.get("interactions") else {}
    user_status = last_interaction.get("user_status", "unknown")

    try:
        result = handle_reply(request.reply, last_action)

        intent = interpret_reply(request.reply)
        if intent == "positive":
            update_user_status(request.context_id, "accepted")
            update_conversation_state(request.context_id, status="active", last_message=request.reply)
        elif intent == "negative":
            update_user_status(request.context_id, "rejected")
            update_conversation_state(request.context_id, status="closed", last_message=request.reply)

        # Produce reply event
        reply_event = UserReplyReceivedEvent(
            payload={"reply": request.reply, "intent": intent},
            context_id=request.context_id,
            merchant_id=merchant_id
        )
        produce_event("reply_events", reply_event.to_dict())

        increment_metric("successful_responses")
        latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
        log_response(request_id, "/v1/reply", "success", latency_ms, f"intent:{intent}")
        return result
        
    except Exception as e:
        increment_metric("failed_responses")
        log_error(request_id, "/v1/reply", e, str(e.__traceback__))
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "error",
            "rationale": "Internal error occurred"
        }