import json
from pathlib import Path

# ============================================================
# DATA PATH
# ============================================================

DATA_DIR = Path(__file__).parent / "data"


# ============================================================
# LOAD PROPERTIES
# ============================================================

def load_properties():
    """Load all properties."""

    with open(DATA_DIR / "properties.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# PROPERTY SEARCH
# ============================================================

def search_properties(
    location=None,
    max_price=None,
    bhk=None,
    min_rating=None,
    pet_friendly=None,
    min_area=None,
    max_metro_distance=None
):
    """
    Intelligent property search.

    Filters:
    - location
    - budget
    - bhk
    - rating
    - pet friendly
    - minimum area
    - metro distance
    """

    properties = load_properties()

    results = []

    for prop in properties:

        # -----------------------------------------
        # Location
        # -----------------------------------------

        if location:

            if prop["location"].lower() != location.lower():

                continue

        # -----------------------------------------
        # Budget
        # -----------------------------------------

        if max_price is not None:

            if prop["price"] > max_price:

                continue

        # -----------------------------------------
        # BHK
        # -----------------------------------------

        if bhk is not None:

            if prop["bhk"] != bhk:

                continue

        # -----------------------------------------
        # Rating
        # -----------------------------------------

        if min_rating is not None:

            if prop.get("rating", 0) < min_rating:

                continue

        # -----------------------------------------
        # Pet Friendly
        # -----------------------------------------

        if pet_friendly is True:

            if not prop.get("pet_friendly", False):

                continue

        # -----------------------------------------
        # Area
        # -----------------------------------------

        if min_area is not None:

            if prop.get("area_sqft", 0) < min_area:

                continue

        # -----------------------------------------
        # Metro Distance
        # -----------------------------------------

        if max_metro_distance is not None:

            if prop.get("metro_distance", 99999) > max_metro_distance:

                continue

        results.append(prop)

    # -----------------------------------------
    # Sort Results
    # -----------------------------------------

    results.sort(
        key=lambda x: (
            -x.get("rating", 0),
            x.get("price", 999999999)
        )
    )

    return results


# ============================================================
# PROPERTY STATISTICS
# ============================================================

def property_statistics(properties):

    if not properties:

        return {
            "count": 0,
            "average_price": 0,
            "average_rating": 0
        }

    avg_price = sum(p["price"] for p in properties) / len(properties)

    avg_rating = sum(
        p.get("rating", 0)
        for p in properties
    ) / len(properties)

    return {

        "count": len(properties),

        "average_price": round(avg_price),

        "average_rating": round(avg_rating, 2)

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    properties = search_properties(
        location="Whitefield",
        max_price=9000000,
        bhk=2
    )

    print(f"\nFound {len(properties)} properties\n")

    for p in properties:

        print(
            f"{p['name']} | "
            f"₹{p['price']:,} | "
            f"{p['rating']}⭐"
        )

    print("\nStatistics\n")

    print(property_statistics(properties))