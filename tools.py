import json
from pathlib import Path
from mock_data import search_properties

DATA_DIR = Path(__file__).parent / "data"


def _load(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------
# Property Search
# ----------------------------
def property_search(location=None, max_price=None, bhk=None):
    return search_properties(
        location=location,
        max_price=max_price,
        bhk=bhk
    )


# ----------------------------
# Neighbourhood
# ----------------------------
def get_neighbourhood_profile(location):
    data = _load("neighbourhoods.json")

    for item in data:
        if item["location"].lower() == location.lower():
            return item

    return {"error": "Location not found"}


# ----------------------------
# Schools
# ----------------------------
def get_school_ratings(location):
    data = _load("schools.json")

    for item in data:
        if item["location"].lower() == location.lower():
            return item["schools"]

    return []


# ----------------------------
# Commute
# ----------------------------
def estimate_commute(source, destination):
    data = _load("commute.json")

    for item in data:
        if (
            item["from"].lower() == source.lower()
            and item["to"].lower() == destination.lower()
        ):
            return item

    return {"time_min": 999, "mode": "unknown"}


# ----------------------------
# Price History
# ----------------------------
def get_price_history(location):
    data = _load("price_history.json")

    for item in data:
        if item["location"].lower() == location.lower():
            return item["trend"]

    return []


# ----------------------------
# Affordability
# ----------------------------
def calculate_affordability(budget, property_price):

    if budget >= property_price:
        return {
            "affordable": True,
            "remaining_budget": budget - property_price
        }

    return {
        "affordable": False,
        "shortfall": property_price - budget
    }