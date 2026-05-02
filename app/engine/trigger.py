def interpret_trigger(trigger: dict) -> dict:
    trigger_type = trigger.get("type", "") or trigger.get("kind", "")
    trigger_type = trigger_type.lower()
    
    if "research" in trigger_type or "curious" in trigger_type or "trend" in trigger_type:
        normalized_type = "research"
    elif "category_seasonal" in trigger_type or "demand_shift" in trigger_type:
        normalized_type = "research"
    elif "search" in trigger_type:
        normalized_type = "search_spike"
    elif "footfall" in trigger_type or ("drop" in trigger_type and "perf" not in trigger_type):
        normalized_type = "footfall_drop"
    elif "festival" in trigger_type and "category" not in trigger_type:
        normalized_type = "festival"
    elif "compliance" in trigger_type:
        normalized_type = "compliance"
    elif "capacity" in trigger_type or "peak" in trigger_type:
        normalized_type = "capacity_peak"
    elif "ipl" in trigger_type or "match" in trigger_type:
        normalized_type = "ipl_match_day"
    elif "sales" in trigger_type or "revenue" in trigger_type:
        normalized_type = "low_sales"
    elif "rating" in trigger_type:
        normalized_type = "rating_drop"
    elif "recall" in trigger_type:
        normalized_type = "recall_due"
    elif "planning" in trigger_type or "appointment" in trigger_type:
        normalized_type = "planning_intent"
    elif "perf_dip" in trigger_type or "perf_spike" in trigger_type:
        normalized_type = "perf_dip"
    elif "lapsed" in trigger_type:
        normalized_type = "customer_lapsed"
    elif "dormant" in trigger_type or "dormancy" in trigger_type:
        normalized_type = "seasonal_dip"
    elif "competitor" in trigger_type:
        normalized_type = "competitor_opened"
    elif "review" in trigger_type:
        normalized_type = "review_theme_emerged"
    elif "renewal" in trigger_type or "trial" in trigger_type:
        normalized_type = "renewal_due"
    elif "chronic" in trigger_type or "refill" in trigger_type:
        normalized_type = "chronic_refill_due"
    elif "winback" in trigger_type:
        normalized_type = "customer_lapsed"
    elif "milestone" in trigger_type:
        normalized_type = "milestone_reached"
    else:
        normalized_type = "unknown"
    
    return {"trigger_type": normalized_type}