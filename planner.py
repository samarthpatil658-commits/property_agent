class AIPlanner:
    """Builds an execution plan from the buyer profile without executing tools."""

    def create_plan(self, buyer):
        return [item["tool"] for item in self.create_plan_details(buyer)]

    def create_plan_details(self, buyer):
        candidates = [
            {
                "tool": "property_search",
                "priority": 100,
                "reason": "Find properties that match locality, budget, and BHK.",
                "required": True,
                "run": True,
            },
            {
                "tool": "estimate_commute",
                "priority": 85,
                "reason": "Estimate daily travel from each property to the buyer office.",
                "required": False,
                "run": bool(buyer.get("office")),
            },
            {
                "tool": "get_school_ratings",
                "priority": 78,
                "reason": "Check school access because family or school priority is present.",
                "required": False,
                "run": bool(buyer.get("school_priority") or (buyer.get("family_size") or 0) >= 3),
            },
            {
                "tool": "get_neighbourhood_profile",
                "priority": 72,
                "reason": "Evaluate safety, metro access, parks, and neighbourhood quality.",
                "required": False,
                "run": self._needs_neighbourhood(buyer),
            },
            {
                "tool": "get_price_history",
                "priority": 66,
                "reason": "Check appreciation trend and investment potential.",
                "required": False,
                "run": bool(buyer.get("investment_priority")),
            },
        ]

        selected = [item for item in candidates if item["run"]]
        selected.sort(key=lambda item: item["priority"], reverse=True)
        return [
            {
                "tool": item["tool"],
                "reason": item["reason"],
                "priority": item["priority"],
                "required": item["required"],
            }
            for item in selected
        ]

    def explain_plan(self, tools):
        reasons = {
            "property_search": "Searching matching properties.",
            "estimate_commute": "Checking office commute.",
            "get_school_ratings": "Finding nearby schools.",
            "get_neighbourhood_profile": "Analysing neighbourhood, safety, metro, and lifestyle fit.",
            "get_price_history": "Checking investment potential.",
        }
        return [reasons.get(tool, f"Running {tool}.") for tool in tools]

    def skipped_tools(self, buyer):
        selected = set(self.create_plan(buyer))
        all_tools = {
            "estimate_commute": "Skipped because no office or commute anchor is known.",
            "get_school_ratings": "Skipped because schools/family were not priorities.",
            "get_neighbourhood_profile": "Skipped because metro, safety, pets, and lifestyle were not emphasized.",
            "get_price_history": "Skipped because investment was not a stated priority.",
        }
        return [
            {"tool": tool, "reason": reason}
            for tool, reason in all_tools.items()
            if tool not in selected
        ]

    def _needs_neighbourhood(self, buyer):
        lifestyle = buyer.get("lifestyle") or []
        return bool(
            buyer.get("metro_priority")
            or buyer.get("pet_friendly")
            or buyer.get("investment_priority")
            or any(item in lifestyle for item in ["quiet", "green", "walkable", "family friendly", "gated community"])
        )


if __name__ == "__main__":
    buyer = {
        "budget": 9000000,
        "bhk": 3,
        "office": "Electronic City",
        "school_priority": True,
        "metro_priority": True,
        "investment_priority": False,
        "pet_friendly": True,
        "family_size": 4,
        "lifestyle": ["family friendly"],
    }
    planner = AIPlanner()
    print(planner.create_plan_details(buyer))
