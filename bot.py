from typing import Optional
from app.engine.message_engine import generate_message

def compose(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> dict:
    """
    Official Challenge Entry Point.
    
    Inputs:
        category: dict (CategoryContext)
        merchant: dict (MerchantContext)
        trigger: dict (TriggerContext)
        customer: Optional[dict] (CustomerContext)
        
    Returns:
        dict: {body, cta, send_as, suppression_key, rationale}
    """
    # 1. Prepare internal action object for the engine
    # The engine expects a normalized context structure
    context = {
        "context": merchant,
        "trigger": trigger,
        "customer": customer or {}
    }
    
    # 2. Determine intent and target
    # This logic matches our decider.py logic
    intent_map = {
        "recall_due": "nudge_recall_action",
        "research_digest": "share_research_insight",
        "search_spike": "share_research_insight",
        "customer_lapsed": "winback_customer",
        "seasonal_dip": "advise_business_strategy",
        "planning_intent": "provide_execution_plan"
    }
    
    trigger_type = trigger.get("type") or trigger.get("kind", "unknown")
    intent = intent_map.get(trigger_type, "share_research_insight")
    
    # Customer targets for winbacks
    target = "customer" if trigger_type == "customer_lapsed" else "merchant"
    
    # 3. Call our High-Fidelity Engine
    action = {
        "intent": intent,
        "target": target,
        "context": context,
        "suppression_key": f"{merchant.get('merchant_id', 'unknown')}_{intent}_{trigger_type}"
    }
    
    result = generate_message(action)
    
    # 4. Final Schema Alignment for Challenge Submission
    return {
        "body": result.get("message"),
        "cta": result.get("cta"),
        "send_as": result.get("send_as"),
        "suppression_key": result.get("suppression_key"),
        "rationale": result.get("rationale")
    }

if __name__ == "__main__":
    # Example execution if run standalone
    print("Vera Bot Engine v2.4 (Root Entry) - Use compose() for evaluation.")
