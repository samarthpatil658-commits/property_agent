import unittest

from ui_state import (
    ensure_ui_state,
    find_property_item,
    selected_items,
    set_selected_property,
    toggle_property_id,
)


class UIStateTests(unittest.TestCase):
    def test_ensure_ui_state_adds_defaults_without_sharing_lists(self):
        first = {}
        second = {}

        ensure_ui_state(first)
        ensure_ui_state(second)
        first["shortlist"].append(1)

        self.assertEqual(first["messages"], [])
        self.assertEqual(second["shortlist"], [])
        self.assertIsNone(first["selected_property_id"])

    def test_toggle_property_id_adds_removes_and_respects_limit(self):
        state = {"compare": []}

        self.assertTrue(toggle_property_id(state, "compare", 1, limit=3))
        self.assertTrue(toggle_property_id(state, "compare", 2, limit=3))
        self.assertTrue(toggle_property_id(state, "compare", 3, limit=3))
        self.assertTrue(toggle_property_id(state, "compare", 4, limit=3))

        self.assertEqual(state["compare"], [2, 3, 4])
        self.assertFalse(toggle_property_id(state, "compare", 3, limit=3))
        self.assertEqual(state["compare"], [2, 4])

    def test_selected_and_find_helpers_return_matching_result_items(self):
        result = {
            "results": [
                {"property": {"id": 1, "name": "A"}},
                {"property": {"id": 2, "name": "B"}},
            ]
        }

        state = {}
        set_selected_property(state, 2)

        self.assertEqual(find_property_item(result, state["selected_property_id"])["property"]["name"], "B")
        self.assertEqual([item["property"]["name"] for item in selected_items(result, [1, 2])], ["A", "B"])
        self.assertEqual(selected_items(result, []), [])


if __name__ == "__main__":
    unittest.main()
