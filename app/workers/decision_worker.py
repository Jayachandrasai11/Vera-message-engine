import json
from ..events.schemas import TriggerReceivedEvent, parse_event, ActionExecutedEvent
from ..store.memory import get_context
from ..engine.decider import decide_action
from ..engine.message_engine import generate_message
from ..events.producer import produce_event
from ..reliability import log_error, is_suppressed, set_suppression


def process_trigger_event(data: dict) -> dict:
    """Process TRIGGER_RECEIVED events."""
    try:
        event = parse_event(data)
        
        context_id = event.context_id
        payload = event.payload
        trigger = payload.get("trigger", {})
        merchant_id = event.merchant_id or "unknown"
        
        stored = get_context(context_id)
        if not stored:
            return {
                "status": "error",
                "error": "Context not found"
            }
        
        merchant = stored.get("payload", {}).get("merchant", {})
        category = stored.get("payload", {}).get("category", {})
        
        # Run normalization (simplified)
        from ..engine.validation import build_sanitized_structure
        normalized = build_sanitized_structure(
            {"merchant": merchant, "category": category},
            trigger
        )
        
        normalized_data = {
            "normalized": {
                "context": normalized["normalized"]["context"],
                "trigger": normalized["normalized"]["trigger"],
                "customer": normalized["normalized"]["trigger"].get("customer", {})
            }
        }
        
        result = decide_action(normalized_data)
        
        if result.get("actions"):
            action = result["actions"][0]
            
            # Check suppression
            suppression_key = action.get("suppression_key", "unknown")
            if is_suppressed(merchant_id, suppression_key):
                return {
                    "status": "suppressed",
                    "suppression_key": suppression_key
                }
            
            msg_result = generate_message(action)
            set_suppression(merchant_id, suppression_key)
            
            # Produce action event
            action_event = ActionExecutedEvent(
                payload={
                    "action": action,
                    "message_result": msg_result
                },
                context_id=context_id,
                merchant_id=merchant_id
            )
            produce_event("action_events", action_event.to_dict())
            
            return {
                "status": "success",
                "message": msg_result["message"],
                "suppression_key": suppression_key
            }
        
        return {
            "status": "no_action"
        }
        
    except Exception as e:
        log_error("decision_worker", "process", e, str(e.__traceback__))
        return {
            "status": "error",
            "error": str(e)
        }


async def run_decision_worker():
    """Run decision worker."""
    pass