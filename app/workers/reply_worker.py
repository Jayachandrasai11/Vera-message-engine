import json
import logging
from ..events.schemas import UserReplyReceivedEvent, parse_event
from ..store.memory import get_context, update_user_status, update_conversation_state
from ..engine.reply import handle_reply, interpret_reply
from ..reliability import log_error

logger = logging.getLogger("vera")

def process_reply_event(data: dict) -> dict:
    """
    Process USER_REPLY_RECEIVED events with history-aware logic.
    """
    try:
        event = parse_event(data)
        context_id = event.context_id
        reply = event.payload.get("reply", "")
        
        stored = get_context(context_id)
        if not stored:
            return {
                "status": "error",
                "error": "Context not found"
            }
        
        # Extract metadata from context
        last_action = stored.get("last_action", "unknown")
        history = stored.get("interactions", []) # This contains past turns for auto-reply detection
        
        # 1. Generate the response using our enhanced engine
        # handle_reply now detects auto-replies and transitions intent
        result = handle_reply(reply, last_action, history)
        
        # 2. Update session state based on detected intent
        intent = interpret_reply(reply)
        
        if result.get("message") is None and result.get("suppression_key") == "auto_reply_detected":
            # Graceful exit for auto-replies
            update_conversation_state(context_id, status="suppressed_auto_reply")
            logger.info(f"[{context_id}] Auto-reply detected. Turn suppressed.")
        else:
            # Standard status updates
            if intent == "positive":
                update_user_status(context_id, "accepted")
            elif intent == "negative":
                update_user_status(context_id, "rejected")
                
            # Update history with current turn
            update_conversation_state(
                context_id, 
                last_message=reply, 
                last_intent=intent
            )
        
        return {
            "status": "success",
            "reply": reply,
            "intent": intent,
            "result": result
        }
        
    except Exception as e:
        log_error("reply_worker", "process", e, str(e.__traceback__))
        return {
            "status": "error",
            "error": str(e)
        }

async def run_reply_worker():
    """Run reply worker."""
    pass