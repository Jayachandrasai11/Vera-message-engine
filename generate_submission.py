import json
import os
from bot import compose

def run_submission_generation():
    print("🚀 Generating submission.jsonl...")
    
    # Path to the canonical test cases (provided in the challenge dataset)
    test_cases_path = "dataset/test_cases.json"
    output_path = "submission.jsonl"
    
    if not os.path.exists(test_cases_path):
        print(f"❌ Error: {test_cases_path} not found. Please ensure the dataset is in the 'dataset' directory.")
        return

    with open(test_cases_path, "r") as f:
        test_cases = json.load(f)

    results = []
    for case in test_cases:
        test_id = case.get("test_id")
        category = case.get("category", {})
        merchant = case.get("merchant", {})
        trigger = case.get("trigger", {})
        customer = case.get("customer") # Can be None
        
        # Call the official compose function
        output = compose(category, merchant, trigger, customer)
        
        # Add the test_id to the output for the judge
        output["test_id"] = test_id
        results.append(output)

    # Write as JSONL (one JSON object per line)
    with open(output_path, "w") as f:
        for entry in results:
            f.write(json.dumps(entry) + "\n")

    print(f"✅ Success! Generated {len(results)} test cases in {output_path}")
    print("Ready for submission. 🏆")

if __name__ == "__main__":
    run_submission_generation()
