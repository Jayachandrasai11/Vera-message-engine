TRIGGER_INTENT_MAP = {
    "search_spike": "share_research_insight",
    "perf_spike": "share_research_insight",
    "recall_due": "nudge_recall_action",
    "research": "share_research_insight",
    "research_digest": "share_research_insight",
    "customer_lapsed": "winback_customer",
    "customer_lapsed_soft": "winback_customer",
    "seasonal_dip": "advise_business_strategy",
    "dormant_with_vera": "advise_business_strategy",
    "planning_intent": "provide_execution_plan",
    "active_planning_intent": "provide_execution_plan",
    "appointment_tomorrow": "provide_execution_plan",
    "festival": "provide_execution_plan",
    "festival_upcoming": "provide_execution_plan",
    "perf_dip": "advise_business_strategy",
}

PRIORITY_MAP = {
    "recall_due": "high",
    "compliance": "high",
    "customer_lapsed": "medium",
    "planning_intent": "medium",
    "research_digest": "low",
    "seasonal_dip": "low"
}

TARGET_MAP = {
    "recall_due": "merchant",
    "customer_lapsed": "customer",
    "research_digest": "merchant",
    "seasonal_dip": "merchant",
    "planning_intent": "merchant",
    "search_spike": "merchant"
}


def get_target_for_recall(customer: dict) -> str:
    if customer and customer.get("id") and customer.get("last_visit_days", 0) >= 150:
        return "customer"
    return "merchant"


def check_conditions(trigger_type: str, normalized: dict) -> tuple[bool, str]:
    customer = normalized.get("customer", {})
    trigger = normalized.get("trigger", {})
    context = normalized.get("context", {})

    if trigger_type == "recall_due":
        customer_exists = customer and customer.get("id")
        last_visit = customer.get("last_visit_days", 0)
        merchant_id = context.get("merchant_id", "unknown")
        if customer_exists and last_visit >= 150:
            return True, "customers overdue for checkups, opportunity to drive repeat visits"
        # Fallback to merchant-level nudge when customer missing or insufficient data
        return True, "patients likely due, opportunity to drive repeat visits with recall reminder"

    if trigger_type in ["search_spike", "research_digest", "research"]:
        return True, "market intelligence available to drive growth"

    if trigger_type == "customer_lapsed":
        customer_exists = customer and customer.get("id")
        last_visit = customer.get("last_visit_days", 0)
        if customer_exists and last_visit >= 45:
            return True, "customer eligible for winback outreach"
        return False, ""

    if trigger_type == "research_digest":
        category = context.get("category")
        if category:
            return True, "share relevant research insights for category growth"
        return False, ""

    if trigger_type == "seasonal_dip":
        count = trigger.get("count", 0)
        if count and count < 0:
            return True, "seasonal trend detected, advise proactive measures"
        return False, ""

    if trigger_type == "planning_intent":
        keyword = trigger.get("keyword", "")
        # Check payload for intent_topic if keyword not set directly
        if not keyword and "payload" in trigger:
            keyword = trigger["payload"].get("intent_topic", "")
        if keyword:
            return True, "merchant seeking planning input, provide execution guidance"
        return False, ""

    return False, ""


def decide_action(normalized_data: dict) -> dict:
    if not normalized_data:
        return {"actions": []}

    normalized = normalized_data.get("normalized", {})
    if not normalized:
        return {"actions": []}

    context = normalized.get("context", {})
    trigger = normalized.get("trigger", {})
    customer = normalized.get("customer", {})

    trigger_type = trigger.get("type", "") or ""

    if not trigger_type or trigger_type not in TRIGGER_INTENT_MAP:
        return {"actions": []}

    intent = TRIGGER_INTENT_MAP[trigger_type]
    passed, reason = check_conditions(trigger_type, normalized)

    if not passed:
        return {"actions": []}

    priority = PRIORITY_MAP.get(trigger_type, "medium")

    # For recall_due, determine target based on customer eligibility
    if trigger_type == "recall_due":
        target = get_target_for_recall(customer)
    else:
        target = TARGET_MAP.get(trigger_type, "merchant")

    merchant_id = context.get("merchant_id", "unknown")
    # Use correct suppression key format: merchant_id_action_trigger
    suppression_key = f"{merchant_id}_{intent}_{trigger_type}"
    if trigger_type == "recall_due":
        suppression_key = f"{merchant_id}_retention_push_recall_due"

    return {
        "actions": [
            {
                "type": "send_message",
                "target": target,
                "intent": intent,
                "priority": priority,
                "suppression_key": suppression_key,
                "reason": f"{trigger_type} -> {reason}",
                "context": normalized
            }
        ]
    }