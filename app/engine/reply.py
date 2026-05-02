import re

# Industry-standard list of common merchant auto-reply patterns (WhatsApp Business)
AUTO_REPLY_PATTERNS = [
    r"thank you for contacting",
    r"will get back to you",
    r"shukriya",
    r"aapki jaankari ke liye",
    r"automated assistant",
    r"reach out soon",
    r"available right now",
    r"hamari team tak pahuncha",
    r"reply soon"
]

def is_auto_reply(reply: str, history: list = None) -> bool:
    """
    Industry-standard auto-reply detection.
    1. Check against known canned-reply patterns.
    2. Check if the exact same message was sent 2+ times recently (session pollution).
    """
    reply_lower = reply.lower().strip()
    
    # Pattern match detection
    for pattern in AUTO_REPLY_PATTERNS:
        if re.search(pattern, reply_lower):
            return True
            
    # Sequence detection (if the last message from the user was identical)
    if history:
        # Filter for user messages only
        user_messages = [msg.get("message", "").lower().strip() for msg in history if msg.get("sender") == "user"]
        if user_messages and user_messages[-1] == reply_lower:
            return True
            
    return False

def interpret_reply(reply: str) -> str:
    """
    Enhanced intent detection with Hindi-English code-mix support.
    """
    reply_lower = reply.lower().strip()
    
    # Delay Intent
    if any(word in reply_lower for word in ["later", "not now", "tomorrow", "baad mein", "kal"]):
        return "delay"
    
    # Positive Intent (Handoff trigger)
    if any(word in reply_lower for word in ["yes", "ok", "sure", "do it", "go ahead", "karo", "theek hai", "haan", "chalo"]):
        return "positive"
    
    # Negative Intent
    if any(word in reply_lower for word in ["no", "not interested", "stop", "don't", "nahi", "rehne do"]):
        return "negative"
    
    # Query Intent
    if any(word in reply_lower for word in ["what", "why", "how", "?", "kyun", "kaise", "kya"]):
        return "query"
    
    return "unknown"

def handle_reply(reply: str, last_action: str = "unknown", history: list = None) -> dict:
    """
    Production-ready reply handler with auto-reply filtering and intent handoff.
    """
    # 1. First Pass: Detect Auto-Reply Pollution (Tie-breaker requirement)
    if is_auto_reply(reply, history):
        return {
            "message": None, # Signal to stop wasting turns
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "auto_reply_detected",
            "rationale": "Detected merchant auto-reply/canned response. Gracefully exiting turn."
        }

    # 2. Second Pass: Detect Intent
    intent = interpret_reply(reply)
    
    if intent == "positive":
        # Intent Handoff Logic: Move from pitch to confirmation immediately
        if last_action == "push_offer":
            message = "Done! I've activated your offer. You'll start seeing demand capture in your dashboard shortly."
        elif last_action == "improve_reviews":
            message = "Perfect. I'll trigger the review recovery plan now and alert you to any new high-impact ratings."
        elif last_action == "run_campaign":
            message = "Great! Your campaign is live. I'll monitor the reach and give you a performance update in 48 hours."
        else:
            message = f"Acknowledged. Proceeding with your request for {last_action.replace('_', ' ')}."
            
        cta = "Track live results?"
        rationale = f"Positive intent detected -> Automated handoff to {last_action} execution phase."
    
    elif intent == "negative":
        message = "Understood. I've paused this recommendation for now. Is there something else specific I can help you with?"
        cta = "See other growth ideas?"
        rationale = "Negative intent detected. Halting action sequence and offering alternatives."
    
    elif intent == "delay":
        message = "No problem, I know you're busy. I'll nudge you about this again in 24 hours."
        cta = "Set specific time?"
        rationale = "Postponement intent. Setting reminder flag."
    
    elif intent == "query":
        # Contextual clarification based on the last suggested action
        clarifications = {
            "push_offer": "This targets people near your shop who are searching for your services right now on magicpin.",
            "improve_reviews": "This identifies your most loyal customers and asks them for feedback to boost your Google rating.",
            "run_campaign": "This boosts your visibility across our partner network during peak footfall hours."
        }
        message = clarifications.get(last_action, "I help optimize your Google Business Profile to drive more walk-ins and calls.")
        cta = "Want me to start now?"
        rationale = "Information query detected. Providing specific value-prop for the last suggested action."
    
    else:
        # Fallback: Re-anchor the value prop
        message = "I can help automate your growth tasks like offers or reviews so you can focus on your customers. Should we try this?"
        cta = "Try it (2 min)?"
        rationale = "Ambiguous intent. Re-anchoring value proposition with low-friction CTA."
    
    return {
        "message": message,
        "cta": cta,
        "send_as": "Vera",
        "rationale": rationale
    }
