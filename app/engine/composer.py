from typing import Optional

# Category group mapping for tone modifiers
CATEGORY_GROUPS = {
    "healthcare": ["dentist", "clinic", "pharmacy", "doctor", "medical", "dental"],
    "fitness": ["gym", "yoga", "fitness", "wellness"],
    "beauty": ["salon", "spa", "beauty"],
    "food": ["restaurant", "cafe", "food", "diner"]
}

# Tone modifiers by category group
TONE_MODIFIERS = {
    "healthcare": "professional, trust-focused",
    "fitness": "energetic, performance-focused",
    "beauty": "friendly, lifestyle tone",
    "food": "revenue and volume focused",
    "generic": "neutral business tone"
}

# Universal action-driven messages
ACTION_MESSAGES = {
    "push_offer": {
        "insight_no_offers": "Around this time, businesses without active offers often miss ~20–25% of high-intent customers.",
        "insight_has_offers": "Active offers can help capture ~20–25% more walk-ins during demand spikes.",
        "action": "Create a limited-time offer to attract more customers."
    },
    "improve_reviews": {
        "insight_low": "Each 0.5 rating increase can lift visibility by ~30–40% in local search.",
        "insight_ok": "Maintaining a 4.2+ rating helps sustain customer trust and bookings.",
        "action": "Request reviews from recent customers to improve ratings."
    },
    "run_campaign": {
        "insight": "Targeted campaigns typically reach ~35–45% more relevant customers in your area.",
        "action": "Launch a campaign to maximize reach during this period."
    },
    "add_photos": {
        "insight": "Profiles with photos often see ~25–35% higher engagement from new customers.",
        "action": "Add photos to showcase your business better."
    },
    "retention_push": {
        "insight": "Retention campaigns can lift customer lifetime value by ~20–30% through timely follow-ups.",
        "action": "Send a reminder to customers due for a revisit."
    }
}

# CTA by action
ACTION_CTAS = {
    "push_offer": "Create offer?",
    "run_campaign": "Launch campaign?",
    "improve_reviews": "Improve ratings?",
    "add_photos": "Add photos?",
    "retention_push": "Send reminder?"
}

# Universal fallback
FALLBACK_MESSAGE = "Businesses like yours often benefit from small, targeted actions such as offers or campaigns to improve engagement and repeat visits."


def get_category_group(category) -> str:
    """Map category to tone group, returns 'generic' if unknown."""
    if not category:
        return "generic"
    cat_lower = category.lower() if isinstance(category, str) else ""
    for group, keywords in CATEGORY_GROUPS.items():
        for keyword in keywords:
            if keyword in cat_lower:
                return group
    return "generic"


def get_tone_modifier(category) -> str:
    """Get tone modifier for category group."""
    group = get_category_group(category)
    return TONE_MODIFIERS.get(group, TONE_MODIFIERS["generic"])


def compose_message(
    category,
    merchant: dict,
    trigger: dict,
    action: str,
    stored_context: dict = None,
    context_id: str = ""
) -> dict:
    """Generate dynamic message based on action and context."""
    try:
        if not merchant:
            return {
                "message": None,
                "cta": None,
                "send_as": "Vera",
                "suppression_key": "no_action",
                "rationale": "Insufficient data for meaningful action"
            }

        name = merchant.get("name", "") or "there"
        rating = merchant.get("rating", 5.0)
        trigger_type = trigger.get("type", "unknown") or "unknown"
        has_offers = len(merchant.get("offers", [])) > 0
        merchant_id = merchant.get("id", context_id or "unknown")

        if trigger_type == "unknown":
            return {
                "message": "I can suggest a few quick ways to improve your business performance. Want to explore?",
                "cta": "Show ideas?",
                "send_as": "Vera",
                "suppression_key": "unknown_trigger",
                "rationale": "Fallback due to unsupported trigger"
            }

        action_data = ACTION_MESSAGES.get(action)
        if not action_data:
            return {
                "message": None,
                "cta": None,
                "send_as": "Vera",
                "suppression_key": "no_action",
                "rationale": "Insufficient data for meaningful action"
            }

        if action == "push_offer":
            insight = action_data["insight_no_offers"] if not has_offers else action_data["insight_has_offers"]
            action_text = action_data["action"]
        elif action == "improve_reviews":
            insight = action_data["insight_low"] if rating < 4.2 else action_data["insight_ok"]
            action_text = action_data["action"]
        elif action == "run_campaign":
            insight = action_data["insight"]
            action_text = action_data["action"]
        elif action == "add_photos":
            insight = action_data["insight"]
            action_text = action_data["action"]
        elif action == "retention_push":
            insight = action_data["insight"]
            action_text = action_data["action"]
        else:
            insight = f"Action {action} identified for your business."
            action_text = f"Consider {action} for better results."

        trigger_context = ""
        if trigger_type == "footfall_drop":
            trigger_context = " Current footfall is below expected levels."
        elif trigger_type == "search_spike":
            trigger_context = " Demand is spiking based on searches."
        elif trigger_type == "festival":
            trigger_context = " Festive season presents promotional opportunity."
        elif trigger_type == "research":
            trigger_context = " Market research insights available."

        message = f"{name}, {insight} {action_text}{trigger_context}"
        cta = ACTION_CTAS.get(action, "Show ideas?")

        rationale_parts = [trigger_type.replace("_", " ")]
        if rating < 4.2 and action == "improve_reviews":
            rationale_parts.append(f"rating {rating}")
        elif not has_offers and action == "push_offer":
            rationale_parts.append("no offers")
        
        outcome = "drives engagement" if action == "push_offer" else "improves revisit rate" if action == "retention_push" else "enhances visibility"
        context_insight = "repeat visit opportunity" if trigger_type == "recall_due" else "business timing"
        rationale = f"{trigger_type.replace('_', ' ')} + {context_insight} -> {action} {outcome}"

        return {
            "message": message,
            "cta": cta,
            "send_as": "Vera",
            "suppression_key": f"{merchant_id}_{action}_{trigger_type}",
            "rationale": rationale
        }

    except Exception:
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "error",
            "rationale": "Safe fallback due to processing error"
        }