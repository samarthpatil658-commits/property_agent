import json
import unittest
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"


class DataIntegrityTests(unittest.TestCase):
    def test_property_dataset_has_required_fields(self):
        properties = json.loads((DATA_DIR / "properties.json").read_text(encoding="utf-8"))

        self.assertEqual(len(properties), 10)
        required = {
            "id",
            "name",
            "location",
            "bhk",
            "price",
            "area_sqft",
            "rating",
            "metro_distance",
            "school_rating",
            "crime_score",
            "roi",
            "price_growth",
            "pet_friendly",
            "amenities",
        }
        for item in properties:
            self.assertTrue(required.issubset(item), item)
            self.assertGreater(item["price"], 0)
            self.assertGreater(item["area_sqft"], 0)
            self.assertIsInstance(item["amenities"], list)

    def test_supporting_datasets_are_available(self):
        for filename in ["commute.json", "neighbourhoods.json", "price_history.json", "schools.json"]:
            data = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
            self.assertGreater(len(data), 0, filename)


if __name__ == "__main__":
    unittest.main()
