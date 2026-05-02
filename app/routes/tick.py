from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from ..store.memory import get_context, save_last_action, is_suppressed, set_suppression
from ..engine.decider import decide_action
from ..engine.decision import decide_action as score_actions
from ..engine.message_engine import generate_message
from ..engine.composer import compose_message
from ..engine.validation import validate_input, build_sanitized_structure
from ..events.producer import produce_event
from ..events.schemas import TriggerReceivedEvent
from ..reliability import (
    increment_metric, log_request, log_response, log_error,
    generate_request_id, reliability
)

router = APIRouter()


class TickRequest(BaseModel):
    context_id: str
    trigger: dict


@router.post("/tick")
def tick(request: TickRequest):
    start_time = datetime.now().timestamp()
    request_id = generate_request_id()
    
    increment_metric("total_requests")
    
    stored = get_context(request.context_id)
    if not stored:
        increment_metric("failed_responses")
        log_error(request_id, "/v1/tick", Exception("Context not found"))
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "error",
            "rationale": "System could not process request safely"
        }

    merchant_id = stored.get("payload", {}).get("merchant", {}).get("id", "unknown")
    if not reliability.check_rate_limit(merchant_id):
        return reliability.rate_limit_response()

    try:
        validate_input({}, request.trigger, request.context_id)
    except Exception as e:
        increment_metric("failed_responses")
        log_error(request_id, "/v1/tick", e, str(e.__traceback__))
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "error",
            "rationale": f"System could not process request safely: {str(e)}"
        }

    trigger_type = request.trigger.get("type", "unknown") or "unknown"

    payload = stored.get("payload", {})
    merchant = payload.get("merchant", {})
    category = payload.get("category", {})

    normalized = build_sanitized_structure({"merchant": merchant, "category": category}, request.trigger)
    normalized_ctx = normalized["normalized"]["context"]
    normalized_trig = normalized["normalized"]["trigger"]
    customer = normalized_trig.get("customer", {})

    log_request(request_id, "/v1/tick", {
        "context_id": request.context_id,
        "trigger_type": trigger_type,
        "merchant_id": merchant_id
    })

    if trigger_type == "recall_due":
        suppression_key = ""
        target = "merchant"
        
        if customer.get("id") and customer.get("last_visit_days", 0) >= 150:
            target = "customer"
            suppression_key = f"{merchant_id}_retention_push_recall_due"
        else:
            suppression_key = f"{merchant_id}_retention_push_recall_due"

        trigger_event = TriggerReceivedEvent(
            payload={"trigger": request.trigger, "customer": customer},
            context_id=request.context_id,
            merchant_id=merchant_id
        )
        produce_event("trigger_events", trigger_event.to_dict())

        if is_suppressed(merchant_id, suppression_key):
            increment_metric("successful_responses")
            increment_metric("suppression_count")
            latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
            log_response(request_id, "/v1/tick", "suppressed", latency_ms, "message_suppressed")
            return {
                "message": None,
                "cta": None,
                "send_as": "Vera",
                "suppression_key": suppression_key,
                "rationale": "Message suppressed due to recent activity"
            }

        result = generate_message({
            "intent": "nudge_recall_action",
            "target": target,
            "suppression_key": suppression_key,
            "context": {
                "context": normalized_ctx,
                "customer": customer,
                "trigger": normalized_trig
            }
})
        set_suppression(merchant_id, suppression_key)
        
        increment_metric("successful_responses")
        latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
        log_response(request_id, "/v1/tick", "success", latency_ms, result.get("rationale"))
        return result

    normalized_data = {
        "normalized": {
            "context": normalized_ctx,
            "trigger": normalized_trig,
            "customer": customer
        }
    }
    
    result = decide_action(normalized_data)

    if not result.get("actions"):
        # Fallback to action-based engine for non-intent triggers
        normalized_trig_type = normalized_trig.get("type", trigger_type)
        cat_slug = normalized_ctx.get("category", "unknown")
        category_slug = cat_slug.get("slug", cat_slug) if isinstance(cat_slug, dict) else cat_slug
        action_result = score_actions(normalized_ctx, {"type": normalized_trig_type, "count": normalized_trig.get("count", 0)})
        if action_result.get("selected_action"):
            selected = action_result["selected_action"]
            merchant_name = normalized_ctx.get("name", "there")
            merchant = {"name": merchant_name, "rating": normalized_ctx.get("rating", 5.0), "offers": normalized_ctx.get("offers", [])}
            trigger = {"type": normalized_trig_type}
            msg_result = compose_message(category_slug, merchant, trigger, selected, 
                                         stored_context={"merchant": {"id": merchant_id}}, 
                                         context_id=merchant_id)
            set_suppression(merchant_id, msg_result["suppression_key"])
            increment_metric("successful_responses")
            latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
            log_response(request_id, "/v1/tick", "success", latency_ms, msg_result.get("rationale"))
            return msg_result
        
        increment_metric("successful_responses")
        increment_metric("no_action_count")
        latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
        log_response(request_id, "/v1/tick", "no_action", latency_ms, "no_response_required")
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "no_reply",
            "rationale": "No response required"
        }

    action = result["actions"][0]
    suppression_key = action.get("suppression_key", "unknown")
    
    if is_suppressed(merchant_id, suppression_key):
        increment_metric("suppression_count")
        latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
        log_response(request_id, "/v1/tick", "suppressed", latency_ms, "suppressed")
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": suppression_key,
            "rationale": "Message suppressed due to recent activity"
        }

    msg_result = generate_message(action)
    set_suppression(merchant_id, suppression_key)
    
    increment_metric("successful_responses")
    latency_ms = round((datetime.now().timestamp() - start_time) * 1000, 2)
    log_response(request_id, "/v1/tick", "success", latency_ms, msg_result.get("rationale"))
    return msg_result