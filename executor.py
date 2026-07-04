from concurrent.futures import ThreadPoolExecutor, as_completed

from tools import (
    calculate_affordability,
    estimate_commute,
    get_neighbourhood_profile,
    get_price_history,
    get_school_ratings,
    property_search,
)


class ToolExecutor:
    """Executes planner-selected tools and returns enriched property data."""

    def __init__(self, retries=1, max_workers=6):
        self.retries = retries
        self.max_workers = max_workers

    def _run_with_retry(self, fn, *args):
        last_error = None
        for _ in range(self.retries + 1):
            try:
                return fn(*args)
            except Exception as error:
                last_error = error
        return {"error": str(last_error)}

    def execute(self, tools, buyer):
        properties, search_notes = self._search_with_fallbacks(buyer)

        if isinstance(properties, dict) and properties.get("error"):
            return {"properties": [], "errors": [properties["error"]]}

        enriched_properties = []
        for property_data in properties:
            enriched_properties.append(self._enrich_property(property_data, tools, buyer))

        return {"properties": enriched_properties, "search_notes": search_notes}

    def _search_with_fallbacks(self, buyer):
        location = buyer["preferred_locations"][0] if buyer["preferred_locations"] else buyer.get("office")
        budget = buyer.get("budget")
        bhk = buyer.get("bhk")
        attempts = [
            (location, budget, bhk, "Exact locality, budget, and BHK match."),
            (None, budget, bhk, "Expanded beyond the preferred locality."),
            (location, int(budget * 1.1) if budget else budget, bhk, "Allowed a 10% budget stretch in the preferred locality."),
            (None, int(budget * 1.1) if budget else budget, bhk, "Allowed a 10% budget stretch across Bangalore."),
        ]

        notes = []
        seen = set()
        for attempt_location, attempt_budget, attempt_bhk, note in attempts:
            key = (attempt_location, attempt_budget, attempt_bhk)
            if key in seen:
                continue
            seen.add(key)
            properties = self._run_with_retry(
                property_search,
                attempt_location,
                attempt_budget,
                attempt_bhk,
            )
            if properties:
                if note != attempts[0][3]:
                    notes.append(note)
                return properties, notes

        return [], ["No matches found after locality and budget fallback attempts."]

    def _enrich_property(self, property_data, tools, buyer):
        item = {
            "property": property_data,
            "tools_used": ["property_search", "calculate_affordability"],
            "tool_errors": [],
        }

        jobs = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            if "estimate_commute" in tools and buyer.get("office"):
                jobs[pool.submit(self._run_with_retry, estimate_commute, property_data["location"], buyer["office"])] = "commute"

            if "get_school_ratings" in tools:
                jobs[pool.submit(self._run_with_retry, get_school_ratings, property_data["location"])] = "schools"

            if "get_neighbourhood_profile" in tools:
                jobs[pool.submit(self._run_with_retry, get_neighbourhood_profile, property_data["location"])] = "neighbourhood"

            if "get_price_history" in tools:
                jobs[pool.submit(self._run_with_retry, get_price_history, property_data["location"])] = "price_history"

            for future in as_completed(jobs):
                key = jobs[future]
                value = future.result()
                if isinstance(value, dict) and value.get("error"):
                    item["tool_errors"].append({key: value["error"]})
                    continue
                item[key] = value
                item["tools_used"].append(self._tool_name_for_key(key))

        item["affordability"] = calculate_affordability(
            buyer["budget"],
            property_data["price"],
        )
        return item

    def _tool_name_for_key(self, key):
        names = {
            "commute": "estimate_commute",
            "schools": "get_school_ratings",
            "neighbourhood": "get_neighbourhood_profile",
            "price_history": "get_price_history",
        }
        return names.get(key, key)
