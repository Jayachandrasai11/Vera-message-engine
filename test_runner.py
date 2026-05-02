import json
import sys
sys.path.insert(0, '.')

from app.engine.decision import decide_action
from app.engine.composer import compose_message

def run_tests(input_file="dataset/test_cases.json", output_file="dataset/results.json"):
    with open(input_file) as f:
        cases = json.load(f)
    
    results = []
    
    for case in cases:
        context = case["context"]
        trigger = case["trigger"]
        
        decision = decide_action(context, trigger)
        
        message = compose_message(
            category=context["category"]["slug"],
            merchant=context["merchant"],
            trigger=trigger,
            action=decision["selected_action"]
        )
        
        result = {
            "context_id": case["context_id"],
            "input": case,
            "decision": decision,
            "message": message
        }
        results.append(result)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Processed {len(results)} cases")
    return results

if __name__ == "__main__":
    run_tests()
