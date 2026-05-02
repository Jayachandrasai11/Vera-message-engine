from datetime import datetime, timezone, timedelta
from .trigger import interpret_trigger


class ValidationError(Exception):
    pass


def safe_join(parts):
    return " ".join([p for p in parts if p and p.strip()])


def validate_input(context: dict, trigger: dict, context_id: str = None) -> dict:
    if not context and not context_id:
        raise ValidationError("context required or context_id must exist")
    
    if not trigger or not (trigger.get("type") or trigger.get("kind")):
        raise ValidationError("trigger.type or trigger.kind is required")
    
    return {"valid": True}


def normalize_context(context: dict, context_id: str = "unknown") -> dict:
    merchant = context.get("merchant", {}) if context else {}
    category = context.get("category", {}) if context else {}
    
    return {
        "merchant_id": merchant.get("id", context.get("merchant_id", context_id) if context else context_id),
        "name": merchant.get("name", "there"),
        "rating": float(merchant.get("rating", 0.0)),
        "offers": merchant.get("offers", []),
        "category": category if isinstance(category, dict) else {"slug": category} if category else {"slug": "unknown"}
    }


def normalize_trigger(trigger: dict) -> dict:
    keyword = trigger.get("keyword", "") or ""
    count = trigger.get("count", 0)
    customer = trigger.get("customer", {})
    
    # Extract keyword from payload.intent_topic for planning_intent triggers
    if not keyword and "payload" in trigger:
        keyword = trigger["payload"].get("intent_topic", "") or keyword
    
    try:
        count = int(count)
    except (ValueError, TypeError):
        count = 0
    
    trigger_type = trigger.get("type") or trigger.get("kind") or "unknown"
    
    # Normalize trigger type using interpret_trigger
    interpreted = interpret_trigger(trigger)
    normalized_type = interpreted.get("trigger_type", trigger_type)
    
    return {
        "type": normalized_type,
        "keyword": keyword,
        "count": count,
        "customer": customer
    }


def build_sanitized_structure(context: dict, trigger: dict) -> dict:
    normalized_ctx = normalize_context(context)
    normalized_trig = normalize_trigger(trigger)
    
    signals = {
        "has_keyword": bool(normalized_trig["keyword"]),
        "has_count": normalized_trig["count"] > 0,
        "has_offers": len(normalized_ctx["offers"]) > 0
    }
    
    return {
        "normalized": {
            "context": normalized_ctx,
            "trigger": normalized_trig,
            "signals": signals
        }
    }


def format_count(count: int) -> str:
    if count == 1:
        return "1 person"
    elif count > 1:
        return f"{count} people"
    return ""


def safe_string_builder(name: str, keyword: str, count: int, offers: list) -> dict:
    signals = {
        "keyword": keyword if keyword else None,
        "count_text": format_count(count) if count > 0 else None,
        "offer_reference": None
    }
    
    if offers:
        signals["offer_reference"] = f"{offers[0].get('title', 'offer') if offers else 'offer'}"
        offer_title = offers[0].get("title", "") if offers else ""
        if offer_title:
            signals["offer_reference"] = offer_title
    
    return signals


class DuplicateChecker:
    _recent_calls: dict = {}
    
    @classmethod
    def should_suppress(cls, context_id: str, trigger_type: str, window_minutes: int = 5) -> bool:
        key = f"{context_id}_{trigger_type}"
        now = datetime.now(timezone.utc)
        
        if key in cls._recent_calls:
            last_call = cls._recent_calls[key]
            if now - last_call < timedelta(minutes=window_minutes):
                return True
        
        cls._recent_calls[key] = now
        return False
    
    @classmethod
    def reset(cls):
        cls._recent_calls = {}


def get_fallback_response() -> dict:
    return {
        "message": "We're reviewing your account activity. Want me to suggest a quick growth action?",
        "cta": "Show recommendations?",
        "rationale": "Fallback triggered due to unknown event type"
    }


def get_duplicate_response() -> dict:
    return {
        "message": "Already shared this suggestion recently. Want new ideas?",
        "cta": "Show new action?",
        "rationale": "Duplicate suppression activated"
    }


