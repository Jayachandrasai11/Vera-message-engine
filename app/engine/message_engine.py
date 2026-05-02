from typing import Optional


INTENT_TEMPLATES = {
    "nudge_recall_action": {
        "merchant": {
            "template": "{name}, several patients are likely due for their 6-month checkups around this time. Sending a recall reminder now can help improve repeat visits by ~20–25%.",
            "cta": "Send reminder?",
            "rationale": "recall_due + repeat visit opportunity -> retention_push to improve revisit rate"
        },
        "customer": {
            "template": "{name}, this is a friendly reminder about your 6-month checkup due now.",
            "cta": "Book appointment?",
            "rationale": "recall_due -> patient due for checkup"
        }
    },
    "winback_customer": {
        "customer": {
            "template": "Hi {name}, we noticed you haven't visited us in a while. No pressure - we're here whenever you're ready to come back.",
            "cta": "Book return visit?",
            "rationale": "customer_lapsed -> gentle reconnection attempt"
        }
    },
    "share_research_insight": {
        "merchant": {
            "template": "Quick insight: {category} in your area are seeing {trend}. Targeted actions can improve visibility by ~30–40%.",
            "cta": "Share insights?",
            "rationale": "research_digest -> share relevant market intelligence"
        }
    },
    "advise_business_strategy": {
        "merchant": {
            "template": "We're seeing a seasonal dip - many merchants pivot to retention campaigns during this period. This can improve customer lifetime value by ~20–30%.",
            "cta": "Show plan?",
            "rationale": "seasonal_dip -> recommend proactive business strategy"
        }
    },
    "provide_execution_plan": {
        "merchant": {
            "template": "For your {keyword} plans: 1) Define scope, 2) Allocate budget, 3) Set timeline. Following this can improve execution success by ~35–45%.",
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
    
    template_data = INTENT_TEMPLATES.get(intent, {}).get(target)
    
    if not template_data:
        merchant_name = merchant_ctx.get("name", "there")
        return {
            "message": f"{merchant_name}, targeted actions like offers or campaigns can improve engagement by 25%.",
            "cta": "Show ideas?",
            "send_as": "Vera",
            "suppression_key": action.get("suppression_key", "unknown"),
            "rationale": "General engagement"
        }
    
    template = template_data["template"]
    cta = template_data["cta"]
    rationale = template_data["rationale"]
    
    name = merchant_ctx.get("name", "")
    if target == "customer" and customer.get("name"):
        name = customer.get("name", "")
    
    category = merchant_ctx.get("category", "")
    trigger = context.get("trigger", {})
    keyword = trigger.get("keyword", "")
    trend = trigger.get("count", 0)
    
    message = template.format(
        name=name,
        category=category,
        keyword=keyword,
        trend=f"{trend}+ searches" if trend > 0 else "high demand"
    )
    
    suppression_key = action.get("suppression_key", f"unknown_{intent}")
    
    return {
        "message": message,
        "cta": cta,
        "send_as": "Vera",
        "suppression_key": suppression_key,
        "rationale": rationale
    }