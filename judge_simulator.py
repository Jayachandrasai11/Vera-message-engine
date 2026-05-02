import json

def score_relevance(trigger_type, action, message):
    keywords = {
        "search_spike": ["searches", "demand", "offer", "promote", "push", "active"],
        "footfall_drop": ["footfall", "walk-ins", "offer", "recovery", "boost", "gym"],
        "festival": ["seasonal", "offer", "promotion", "deal"],
        "compliance": ["reviews", "rating", "listing", "improve"],
        "research": ["photos", "profile", "listing", "add", "image"]
    }
    
    relevant = keywords.get(trigger_type, ["offer", "campaign"])
    score = 0
    msg_lower = message.lower()
    for kw in relevant:
        if kw in msg_lower:
            score += 1
    return min(score, 5)

def score_specificity(message, context):
    score = 0
    if "%" in message or "~" in message:
        score += 2
    if any(d in message for d in ["15-20", "23%", "30%", "25%", "repeat visits", "LTV"]):
        score += 2
    if context.get("merchant", {}).get("rating"):
        score += 1
    return min(score, 5)

def score_business_impact(action, message):
    action_words = {
        "push_offer": ["offer", "deal", "promote", "push", "discount", "push_offer"],
        "improve_reviews": ["review", "rating", "visibility", "trust", "improve"],
        "run_campaign": ["campaign", "growth", "launch", "run", "volume"],
        "retention_push": ["retention", "repeat", "visit", "member", "loyalty"],
        "add_photos": ["photo", "profile", "image", "listing"]
    }
    
    words = action_words.get(action, ["offer", "campaign", "help"])
    count = sum(1 for w in words if w in message.lower())
    return min(count + 1, 5)

def score_clarity(message):
    score = 0
    if 30 <= len(message) <= 250:
        score += 2
    if "?" in message:
        score += 1
    if "want me to" in message.lower():
        score += 2
    return min(score, 5)

def judge_case(result):
    msg = result.get("message", {}).get("message", "")
    if not msg:
        return {"relevance": 0, "specificity": 0, "impact": 0, "clarity": 0, "total": 0}
    
    trigger = result.get("input", {}).get("trigger", {}).get("type", "")
    action = result.get("decision", {}).get("selected_action", "")
    context = result.get("input", {}).get("context", {})
    
    r = score_relevance(trigger, action, msg)
    s = score_specificity(msg, context)
    i = score_business_impact(action, msg)
    c = score_clarity(msg)
    
    return {
        "relevance": r,
        "specificity": s,
        "impact": i,
        "clarity": c,
        "total": r + s + i + c
    }

def run_judge(results_file="dataset/results.json", output_file="dataset/judge_scores.json"):
    with open(results_file) as f:
        results = json.load(f)
    
    scored = []
    for r in results:
        scores = judge_case(r)
        r["judge_score"] = scores
        scored.append(r)
    
    with open(output_file, "w") as f:
        json.dump(scored, f, indent=2)
    
    total = sum(r["judge_score"]["total"] for r in scored)
    avg = total / len(scored)
    
    low = sorted(scored, key=lambda x: x["judge_score"]["total"])[:5]
    top = sorted(scored, key=lambda x: x["judge_score"]["total"], reverse=True)[:5]
    
    summary = {
        "avg_score": round(avg, 2),
        "min_score": min(r["judge_score"]["total"] for r in scored),
        "max_score": max(r["judge_score"]["total"] for r in scored),
        "total_cases": len(scored),
        "low_cases": [{"id": r["context_id"], "score": r["judge_score"]["total"]} for r in low],
        "top_cases": [{"id": r["context_id"], "score": r["judge_score"]["total"]} for r in top]
    }
    
    with open("dataset/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"Average Score: {avg:.2f}")
    print(f"Summary saved to dataset/summary.json")
    return summary

if __name__ == "__main__":
    run_judge()
