def analyze_merchant(merchant: dict, category: dict, trigger_type: str) -> dict:
    peer_stats = category.get("peer_stats", {})
    avg_rating = peer_stats.get("avg_rating", 0)
    avg_reviews = peer_stats.get("avg_review_count", 0)
    
    merchant_rating = merchant.get("rating", 0)
    merchant_reviews = merchant.get("review_count", 0)
    
    rating_gap = merchant_rating - avg_rating
    low_rating = merchant_rating < avg_rating
    low_reviews = merchant_reviews < avg_reviews
    
    offers = merchant.get("offers", [])
    has_offer = len(offers) > 0
    
    high_demand = trigger_type == "search_spike"
    
    metrics = merchant.get("metrics", {})
    peer_metrics = category.get("peer_stats", {})
    merchant_views = metrics.get("views", 0)
    merchant_photos = metrics.get("photos", 0)
    avg_views = peer_metrics.get("avg_views", 0)
    avg_photos = peer_metrics.get("avg_photos", 0)
    
    low_visibility = merchant_views < avg_views or merchant_photos < avg_photos
    
    return {
        "rating_gap": rating_gap,
        "low_rating": low_rating,
        "low_reviews": low_reviews,
        "has_offer": has_offer,
        "high_demand": high_demand,
        "low_visibility": low_visibility
    }