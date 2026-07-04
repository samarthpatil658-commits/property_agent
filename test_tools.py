import unittest

from executor import ToolExecutor
from planner import AIPlanner
from ranking import RankingEngine
from tools import (
    calculate_affordability,
    estimate_commute,
    get_neighbourhood_profile,
    get_price_history,
    get_school_ratings,
    property_search,
)


class ToolTests(unittest.TestCase):
    def test_property_search_and_enrichment_tools(self):
        properties = property_search(location="Whitefield", max_price=9_000_000)
        self.assertEqual([item["name"] for item in properties], ["Green Heights", "Tech Park Residency"])

        self.assertEqual(get_neighbourhood_profile("Whitefield")["location"], "Whitefield")
        self.assertGreaterEqual(len(get_school_ratings("Whitefield")), 1)
        self.assertEqual(estimate_commute("Whitefield", "Electronic City")["time_min"], 45)
        self.assertEqual(get_price_history("Whitefield")[0], 6500)
        self.assertTrue(calculate_affordability(9_000_000, 8_500_000)["affordable"])


class PlannerExecutorRankingTests(unittest.TestCase):
    def _buyer(self):
        return {
            "budget": 9_000_000,
            "bhk": 3,
            "property_type": "Apartment",
            "preferred_locations": ["Electronic City"],
            "office": "Electronic City",
            "family_size": None,
            "school_priority": True,
            "metro_priority": True,
            "investment_priority": True,
            "pet_friendly": True,
            "ready_to_move": None,
            "lifestyle": ["Quiet", "Gated Community"],
            "amenities": [],
        }

    def test_planner_selects_tools_from_buyer_priorities(self):
        planner = AIPlanner()
        plan = planner.create_plan(self._buyer())

        self.assertEqual(plan[0], "property_search")
        self.assertIn("estimate_commute", plan)
        self.assertIn("get_school_ratings", plan)
        self.assertIn("get_neighbourhood_profile", plan)
        self.assertIn("get_price_history", plan)

    def test_executor_enriches_properties_and_tracks_tools(self):
        buyer = self._buyer()
        plan = AIPlanner().create_plan(buyer)

        results = ToolExecutor().execute(plan, buyer)

        self.assertEqual(len(results["properties"]), 1)
        item = results["properties"][0]
        self.assertEqual(item["property"]["name"], "Prestige Sunrise")
        self.assertIn("affordability", item)
        self.assertIn("tools_used", item)
        self.assertIn("estimate_commute", item["tools_used"])
        self.assertIn("get_school_ratings", item["tools_used"])

    def test_ranking_adds_score_confidence_and_explanations(self):
        buyer = self._buyer()
        plan = AIPlanner().create_plan(buyer)
        results = ToolExecutor().execute(plan, buyer)

        ranked = RankingEngine().rank(results, buyer)

        self.assertEqual(len(ranked), 1)
        item = ranked[0]
        self.assertGreaterEqual(item["score"], 80)
        self.assertGreaterEqual(item["confidence"], 80)
        self.assertIn("pros", item)
        self.assertIn("tradeoffs", item)
        self.assertIn("match", item)

    def test_executor_fallback_expands_when_exact_locality_has_no_match(self):
        buyer = self._buyer()
        buyer["preferred_locations"] = ["Indiranagar"]
        buyer["budget"] = 9_000_000

        results = ToolExecutor().execute(["property_search"], buyer)

        self.assertGreaterEqual(len(results["properties"]), 1)
        self.assertTrue(results["search_notes"])
        self.assertIn("Expanded", results["search_notes"][0])


if __name__ == "__main__":
    unittest.main()
