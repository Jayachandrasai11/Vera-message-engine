from app.engine.decision import decide_action, score_action
from app.store.memory import (
    store_context, get_context, save_last_action, update_user_status,
    is_recently_sent, get_last_interaction, PIVOT_ACTIONS
)
from app.engine.validation import (
    validate_input, normalize_context, normalize_trigger,
    DuplicateChecker, get_fallback_response, get_duplicate_response, ValidationError
)
import unittest


class TestScoreAction(unittest.TestCase):
    def test_search_spike_boost_push_offer(self):
        context = {"merchant": {"rating": 4.5, "offers": []}, "category": {"slug": "restaurants"}}
        trigger = {"type": "search_spike"}
        self.assertEqual(score_action("push_offer", context, trigger), 24)

    def test_rating_drop_boost_improve_reviews(self):
        context = {"merchant": {"rating": 4.5, "offers": []}, "category": {"slug": "restaurants"}}
        trigger = {"type": "rating_drop"}
        self.assertEqual(score_action("improve_reviews", context, trigger), 20)

    def test_capacity_peak_boost_run_campaign(self):
        context = {"merchant": {"rating": 4.5, "offers": []}, "category": {"slug": "dentists"}}
        trigger = {"type": "capacity_peak"}
        self.assertEqual(score_action("run_campaign", context, trigger), 18)

    def test_capacity_peak_boost_run_campaign_gyms(self):
        context = {"merchant": {"rating": 4.5, "offers": []}, "category": {"slug": "gyms"}}
        trigger = {"type": "capacity_peak"}
        self.assertEqual(score_action("run_campaign", context, trigger), 18)

    def test_low_rating_from_merchant_condition(self):
        context = {"merchant": {"rating": 4.0, "offers": []}, "category": {}}
        trigger = {"type": "unknown"}
        self.assertEqual(score_action("improve_reviews", context, trigger), 15)

    def test_offer_exists_boost_push_offer(self):
        context = {"merchant": {"rating": 4.5, "offers": [{"title": "Deal"}]}, "category": {}}
        trigger = {"type": "search_spike"}
        self.assertEqual(score_action("push_offer", context, trigger), 21)

    def test_gyms_category_retention_push(self):
        context = {"merchant": {"rating": 4.5, "offers": []}, "category": {"slug": "gyms"}}
        trigger = {"type": "unknown"}
        self.assertEqual(score_action("retention_push", context, trigger), 11)

    def test_restaurants_category_run_campaign(self):
        context = {"merchant": {"rating": 4.5, "offers": []}, "category": {"slug": "restaurants"}}
        trigger = {"type": "unknown"}
        self.assertEqual(score_action("run_campaign", context, trigger), 14)


class TestDecideAction(unittest.TestCase):
    def test_returns_action_and_scores(self):
        context = {"merchant": {}, "category": {}}
        trigger = {"type": "unknown"}
        result = decide_action(context, trigger)
        self.assertIn("selected_action", result)
        self.assertIn("all_scores", result)
        self.assertEqual(result["selected_action"], "push_offer")

    def test_deterministic_output(self):
        context = {"merchant": {"rating": 3.8, "offers": []}, "category": {"slug": "gyms"}}
        trigger = {"type": "rating_drop"}
        result1 = decide_action(context, trigger)
        result2 = decide_action(context, trigger)
        self.assertEqual(result1["selected_action"], result2["selected_action"])
        self.assertEqual(result1["all_scores"], result2["all_scores"])

    def test_search_spike_to_push_offer(self):
        context = {
            "merchant": {"rating": 4.5, "offers": [{"title": "Deal"}]},
            "category": {"slug": "dentists"}
        }
        trigger = {"type": "search_spike", "keyword": "root canal"}
        result = decide_action(context, trigger)
        self.assertEqual(result["selected_action"], "push_offer")

    def test_fallback_when_zero_scores(self):
        context = {"merchant": {"rating": 5.0, "offers": []}, "category": {"slug": "unknown"}}
        trigger = {"type": "unknown"}
        result = decide_action(context, trigger)
        self.assertEqual(result["selected_action"], "push_offer")


class TestMemory(unittest.TestCase):
    def test_store_and_retrieve_context(self):
        store_context("test", "mem_test_1", 1, {"merchant": {"name": "Test"}})
        result = get_context("mem_test_1")
        self.assertIsNotNone(result)
        self.assertEqual(result["payload"]["merchant"]["name"], "Test")

    def test_save_last_action(self):
        store_context("test", "mem_test_2", 1, {})
        save_last_action("mem_test_2", "push_offer", {"type": "search_spike"}, "Test msg")
        result = get_context("mem_test_2")
        self.assertEqual(result["last_action"], "push_offer")
        self.assertIn("interactions", result)
        self.assertEqual(result["interactions"][0]["action"], "push_offer")
        self.assertEqual(result["interactions"][0]["user_status"], "pending")

    def test_update_user_status(self):
        store_context("test", "mem_test_3", 1, {})
        save_last_action("mem_test_3", "push_offer", {"type": "search_spike"}, "Test")
        update_user_status("mem_test_3", "accepted")
        result = get_context("mem_test_3")
        self.assertEqual(result["interactions"][0]["user_status"], "accepted")

    def test_is_recently_sent(self):
        store_context("test", "mem_test_4", 1, {})
        save_last_action("mem_test_4", "push_offer", {"type": "search_spike"}, "Test")
        self.assertTrue(is_recently_sent("mem_test_4"))

    def test_pivot_actions(self):
        self.assertEqual(PIVOT_ACTIONS["push_offer"], "improve_reviews")
        self.assertEqual(PIVOT_ACTIONS["improve_reviews"], "push_offer")
        self.assertEqual(PIVOT_ACTIONS["run_campaign"], "push_offer")


class TestValidation(unittest.TestCase):
    def test_normalize_context_full(self):
        ctx = {"merchant": {"id": "m1", "name": "Shop", "rating": 4.5, "offers": []}, "category": {"slug": "retail"}}
        norm = normalize_context(ctx)
        self.assertEqual(norm["merchant_id"], "m1")
        self.assertEqual(norm["name"], "Shop")
        self.assertEqual(norm["rating"], 4.5)
        self.assertEqual(norm["category"], "retail")

    def test_normalize_context_missing(self):
        ctx = {}
        norm = normalize_context(ctx)
        self.assertEqual(norm["name"], "there")
        self.assertEqual(norm["rating"], 0.0)
        self.assertEqual(norm["offers"], [])
        self.assertEqual(norm["category"], "unknown")

    def test_normalize_trigger(self):
        trigger = {"type": "search_spike", "keyword": "pizza", "count": 100}
        norm = normalize_trigger(trigger)
        self.assertEqual(norm["type"], "search_spike")
        self.assertEqual(norm["keyword"], "pizza")
        self.assertEqual(norm["count"], 100)

    def test_normalize_trigger_missing(self):
        trigger = {}
        norm = normalize_trigger(trigger)
        self.assertEqual(norm["type"], "unknown")
        self.assertEqual(norm["keyword"], "")
        self.assertEqual(norm["count"], 0)

    def test_validate_missing_context_id(self):
        with self.assertRaises(ValidationError):
            validate_input({}, {"type": "search_spike"}, None)

    def test_validate_missing_trigger_type(self):
        store_context("test", "val_test", 1, {})
        with self.assertRaises(ValidationError):
            validate_input({}, {}, "val_test")


if __name__ == "__main__":
    unittest.main()
