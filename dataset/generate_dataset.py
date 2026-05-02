import json
import random

CATEGORIES = ["gym", "dentist", "salon", "restaurant", "pharmacy"]
TRIGGERS = ["search_spike", "footfall_drop", "festival", "compliance", "research"]
MERCHANT_NAMES = {
    "gym": ["FitZone", "PowerHouse Gym", "CrossFit Center", "Iron Gym", "Elite Fitness"],
    "dentist": ["Dr. Smith Dental", "Bright Smile Clinic", "Family Dental Care", "Smile Studio", "Tooth Fairy Dental"],
    "salon": ["Style Studio", "Beauty Lounge", "Hair Craft", "Glamour Salon", "Chic Cuts"],
    "restaurant": ["Pizza Palace", "Burger Barn", "Cafe Corner", "Foodie Hub", "Tasty Bites"],
    "pharmacy": ["HealthPlus Pharmacy", "MediCure Drugs", "Wellness Pharmacy", "QuickMeds", "CareFirst Pharmacy"]
}

def generate_dataset(num_cases=80):
    cases = []
    case_id = 1
    
    for category in CATEGORIES:
        for trigger in TRIGGERS:
            ratings = [4.5, 4.2, 4.0, 3.8, 3.5]
            offer_options = [[], [{"title": "20% Off"}]]
            
            for rating in ratings:
                for offers in offer_options:
                    context_id = f"m_{case_id:03d}"
                    merchant_name = random.choice(MERCHANT_NAMES[category])
                    
                    case = {
                        "context_id": context_id,
                        "context": {
                            "merchant": {
                                "id": context_id,
                                "name": merchant_name,
                                "rating": rating,
                                "offers": offers
                            },
                            "category": {"slug": category}
                        },
                        "trigger": {"type": trigger, "count": random.randint(10, 200)}
                    }
                    cases.append(case)
                    case_id += 1
    
    return cases[:num_cases]

if __name__ == "__main__":
    data = generate_dataset(80)
    with open("dataset/test_cases.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} test cases")
