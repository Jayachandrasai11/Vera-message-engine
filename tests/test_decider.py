from app.engine.decider import decide_action, check_conditions, TRIGGER_INTENT_MAP
import unittest


class TestDecider(unittest.TestCase):
    def test_recall_due_triggers_action(self):
        data = {
            "normalized": {
                "context": {"merchant_id": "m_101", "name": "Clinic", "rating": 4.5, "category": "dentists"},
                "trigger": {"type": "recall_due"},
                "customer": {"id": "c_1", "last_visit_days": 160}
            }
        }
        result = decide_action(data)
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0]["intent"], "nudge_recall_action")
        self.assertEqual(result["actions"][0]["priority"], "high")

    def test_recall_due_no_customer(self):
        data = {
            "normalized": {
                "context": {"merchant_id": "m_101", "name": "Clinic"},
                "trigger": {"type": "recall_due"},
                "customer": {}
            }
        }
        result = decide_action(data)
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0]["target"], "merchant")

    def test_recall_due_customer_below_threshold(self):
        data = {
            "normalized": {
                "context": {"merchant_id": "m_101", "name": "Clinic"},
                "trigger": {"type": "recall_due"},
                "customer": {"id": "c_1", "last_visit_days": 100}
            }
        }
        result = decide_action(data)
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0]["target"], "merchant")

    def test_customer_lapsed_triggers(self):
        data = {
            "normalized": {
                "context": {"merchant_id": "m_101", "name": "Clinic"},
                "trigger": {"type": "customer_lapsed"},
                "customer": {"id": "c_1", "last_visit_days": 60}
            }
        }
        result = decide_action(data)
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0]["target"], "customer")

    def test_planning_intent_triggers(self):
        data = {
            "normalized": {
                "context": {"merchant_id": "m_101", "name": "Clinic"},
                "trigger": {"type": "planning_intent", "keyword": "expansion"},
                "customer": {}
            }
        }
        result = decide_action(data)
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0]["intent"], "provide_execution_plan")

    def test_research_digest_triggers(self):
        data = {
            "normalized": {
                "context": {"merchant_id": "m_101", "name": "Clinic", "category": "retail"},
                "trigger": {"type": "research_digest"},
                "customer": {}
            }
        }
        result = decide_action(data)
        self.assertEqual(len(result["actions"]), 1)

    def test_unknown_trigger_no_action(self):
        data = {
            "normalized": {
                "context": {"merchant_id": "m_101"},
                "trigger": {"type": "unknown"},
                "customer": {}
            }
        }
        result = decide_action(data)
        self.assertEqual(len(result["actions"]), 0)

    def test_empty_input_no_action(self):
        result = decide_action({})
        self.assertEqual(len(result["actions"]), 0)


if __name__ == "__main__":
    unittest.main()