from typing import Optional

# Category to Emoji mapping
CATEGORY_EMOJIS = {
    "dentists": "🦷",
    "salons": "✂️",
    "restaurants": "🍕",
    "gyms": "🏋️",
    "pharmacies": "💊",
    "default": "✨"
}

# Situation (Trigger) to Emoji mapping
SITUATION_EMOJIS = {
    "search_spike": "🔥",
    "perf_spike": "🚀",
    "recall_due": "📅",
    "customer_lapsed": "👋",
    "festival": "🎉",
    "festival_upcoming": "🪔",
    "perf_dip": "📉",
    "compliance": "✅",
    "research": "💡",
    "default": "✨"
}

INTENT_TEMPLATES = {
    "nudge_recall_action": {
        "merchant": {
            "template": "{name}, several patients are likely due for their 6-month checkups {situation_emoji}. Sending a recall reminder now can help improve repeat visits by ~20–25%.",
            "cta": "Send reminder?",
            "rationale": "recall_due + repeat visit opportunity -> retention_push to improve revisit rate"
        },
        "customer": {
            "template": "Hi {name}, {merchant_name} here {category_emoji}. It's been a few months since your last visit — your 6-month checkup recall is due {situation_emoji}.",
            "cta": "Book now?",
            "rationale": "recall_due -> patient due for checkup"
        }
    },
    "winback_customer": {
        "customer": {
            "template": "Hi {name}, we noticed you haven't visited us at {merchant_name} in a while {category_emoji}. No pressure - we're here whenever you're ready to come back {situation_emoji}!",
            "cta": "Book return visit?",
            "rationale": "customer_lapsed -> gentle reconnection attempt"
        }
    },
    "share_research_insight": {
        "merchant": {
            "template": "Quick insight {situation_emoji}: {category} in your area are seeing {trend}. Targeted actions can improve visibility by ~30–40%.",
            "cta": "Share insights?",
            "rationale": "research_digest -> share relevant market intelligence"
        }
    },
    "advise_business_strategy": {
        "merchant": {
            "template": "We're seeing a seasonal dip {situation_emoji} - many merchants pivot to retention campaigns during this period. This can improve customer lifetime value by ~20–30%.",
            "cta": "Show plan?",
            "rationale": "seasonal_dip -> recommend proactive business strategy"
        }
    },
    "provide_execution_plan": {
        "merchant": {
            "template": "For your {keyword} plans {situation_emoji}: 1) Define scope, 2) Allocate budget, 3) Set timeline. Following this can improve execution success by ~35–45%.",
            "cta": "Detail plan?",
            "rationale": "planning_intent -> provide structured execution roadmap"
        }
    }
}


def generate_message(action: dict) -> dict:
    if not action:
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "no_reply",
            "rationale": "No response required"
        }
    
    intent = action.get("intent", "")
    target = action.get("target", "merchant")
    context = action.get("context", {})
    merchant_ctx = context.get("context", {})
    customer = context.get("customer", {})
    trigger = context.get("trigger", {})
    
    template_data = INTENT_TEMPLATES.get(intent, {}).get(target)
    
    if not template_data:
        merchant_name = merchant_ctx.get("name", "there")
        return {
            "message": f"{merchant_name}, targeted actions like offers or campaigns can improve engagement by 25% 🔥.",
            "cta": "Show ideas?",
            "send_as": "Vera",
            "suppression_key": action.get("suppression_key", "unknown"),
            "rationale": "General engagement"
        }
    
    template = template_data["template"]
    cta = template_data["cta"]
    rationale = template_data["rationale"]
    
    # 1. Determine Name
    name = merchant_ctx.get("name", "")
    if target == "customer" and customer.get("name"):
        name = customer.get("name", "")
    
    # 2. Determine Category Emoji
    cat_data = merchant_ctx.get("category", "default")
    if isinstance(cat_data, dict):
        cat_slug = cat_data.get("slug", "default")
    else:
        cat_slug = cat_data
    category_emoji = CATEGORY_EMOJIS.get(cat_slug, CATEGORY_EMOJIS["default"])
    
    # 3. Determine Situation Emoji (Dynamic Selection)
    trigger_type = trigger.get("type", "default")
    situation_emoji = SITUATION_EMOJIS.get(trigger_type, SITUATION_EMOJIS["default"])
    
    # 4. Fill Template
    keyword = trigger.get("keyword", "")
    trend = trigger.get("count", 0)
    
    message = template.format(
        name=name,
        merchant_name=merchant_ctx.get("name", "the clinic"),
        category_emoji=category_emoji,
        situation_emoji=situation_emoji,
        category=cat_slug,
        keyword=keyword,
        trend=f"{trend}+ searches" if trend > 0 else "high demand"
    )
    
    suppression_key = action.get("suppression_key", f"unknown_{intent}")
    
    return {
        "message": message,
        "cta": cta,
        "send_as": "merchant_on_behalf" if target == "customer" else "Vera",
        "suppression_key": suppression_key,
        "rationale": rationale
    }