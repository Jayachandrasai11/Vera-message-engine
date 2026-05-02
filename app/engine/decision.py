# Trigger-action relevance scoring for action-based engine

# Action relevance per trigger type (1-5 scale)
TRIGGER_RELEVANCE = {
    "footfall_drop": {
        "push_offer": 5,
        "run_campaign": 4,
        "improve_reviews": 3,
        "add_photos": 2,
        "retention_push": 3
    },
    "festival": {
        "push_offer": 5,
        "run_campaign": 5,
        "improve_reviews": 2,
        "add_photos": 3,
        "retention_push": 4
    },
    "research": {
        "push_offer": 3,
        "run_campaign": 4,
        "improve_reviews": 5,
        "add_photos": 4,
        "retention_push": 2
    },
    "search_spike": {
        "push_offer": 5,
        "run_campaign": 4,
        "improve_reviews": 3,
        "add_photos": 2,
        "retention_push": 3
    },
    "recall_due": {
        "push_offer": 4,
        "run_campaign": 3,
        "improve_reviews": 2,
        "add_photos": 1,
        "retention_push": 5
    },
    "rating_drop": {
        "push_offer": 2,
        "run_campaign": 3,
        "improve_reviews": 5,
        "add_photos": 3,
        "retention_push": 4
    },
    "low_sales": {
        "push_offer": 5,
        "run_campaign": 4,
        "improve_reviews": 3,
        "add_photos": 2,
        "retention_push": 3
    },
    "unknown": {
        "push_offer": 3,
        "run_campaign": 3,
        "improve_reviews": 3,
        "add_photos": 3,
        "retention_push": 3
    }
}

# Available actions
ACTIONS = ["push_offer", "run_campaign", "improve_reviews", "add_photos", "retention_push"]


def score_action(action: str, context: dict, trigger: dict) -> int:
    """Calculate score for an action based on trigger and context."""
    trigger_type = trigger.get("type", "unknown")
    relevance_map = TRIGGER_RELEVANCE.get(trigger_type, TRIGGER_RELEVANCE["unknown"])
    trigger_score = relevance_map.get(action, 3)
    
    # Context factors
    rating = context.get("rating", 5.0)
    has_offers = len(context.get("offers", [])) > 0
    has_photos = context.get("photos", 0) > 0
    
    # Revenue factor (higher for offers when no offers exist)
    if action == "push_offer" and not has_offers:
        revenue = 2
    else:
        revenue = 1
    
    # Ease factor (lower rating = easier to improve reviews)
    if action == "improve_reviews" and rating < 4.2:
        ease = 2
    else:
        ease = 1
    
    # Context factor (photos needed for visual actions)
    if action == "add_photos" and not has_photos:
        context_score = 2
    else:
        context_score = 1
    
    # Final score: trigger*2 + revenue*2 + ease*1 + context*1
    return (trigger_score * 2) + (revenue * 2) + ease + context_score


def decide_action(context: dict, trigger: dict) -> dict:
    """Select the best action based on scores."""
    scores = {}
    for action in ACTIONS:
        scores[action] = score_action(action, context, trigger)
    
    # Sort by score (desc), then by trigger relevance (desc) for tie-breaking
    trigger_type = trigger.get("type", "unknown")
    relevance_map = TRIGGER_RELEVANCE.get(trigger_type, TRIGGER_RELEVANCE["unknown"])
    
    def sort_key(item):
        action, score = item
        return (score, relevance_map.get(action, 0))
    
    best_action = sorted(scores.items(), key=sort_key, reverse=True)[0][0]
    return {"selected_action": best_action, "scores": scores}


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ({"rating": 4.2, "offers": [], "photos": 0}, {"type": "recall_due"}),
        ({"rating": 3.8, "offers": [], "photos": 3}, {"type": "research"}),
        ({"rating": 4.5, "offers": [], "photos": 0}, {"type": "festival"}),
        ({"rating": 4.0, "offers": [], "photos": 0}, {"type": "footfall_drop"}),
    ]
    
    for ctx, trig in test_cases:
        result = decide_action(ctx, trig)
        print(f"{trig['type']} -> {result['selected_action']} (scores: {result['scores']})")