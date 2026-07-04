import unittest

from mock_data import search_properties


class SearchTests(unittest.TestCase):
    def test_search_filters_by_location_budget_and_bhk(self):
        results = search_properties(
            location="Electronic City",
            max_price=9_000_000,
            bhk=3,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Prestige Sunrise")

    def test_search_sorts_by_rating_then_price(self):
        results = search_properties(max_price=9_000_000)

        self.assertGreaterEqual(len(results), 1)
        ratings = [item["rating"] for item in results]
        self.assertEqual(ratings, sorted(ratings, reverse=True))


if __name__ == "__main__":
    unittest.main()
