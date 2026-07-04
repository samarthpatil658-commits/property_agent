import copy
import json
import re


KNOWN_AREAS = [
    "whitefield",
    "electronic city",
    "sarjapur",
    "hebbal",
    "bellandur",
    "marathahalli",
    "koramangala",
    "indiranagar",
    "hsr layout",
    "jp nagar",
    "jayanagar",
    "yelahanka",
    "mahadevapura",
    "itpl",
]


class ConversationManager:
    """Maintains buyer memory and extracts profile signals from conversation."""

    def __init__(self):
        self.reset_profile()

    def reset_profile(self):
        self.profile = {
            "budget": None,
            "bhk": None,
            "property_type": None,
            "preferred_locations": [],
            "office": None,
            "family_size": None,
            "school_priority": False,
            "metro_priority": False,
            "investment_priority": False,
            "pet_friendly": False,
            "ready_to_move": None,
            "lifestyle": [],
            "amenities": [],
        }
        self.history = []
        self.asked_fields = set()

    def get_profile(self):
        return copy.deepcopy(self.profile)

    def get_memory_snapshot(self):
        return {
            "profile": self.get_profile(),
            "asked_fields": sorted(self.asked_fields),
            "turns": len(self.history),
        }

    def record_assistant(self, message):
        if message:
            self.history.append({"role": "assistant", "content": message})

    def update_profile(self, message, llm_client=None, use_llm=True):
        self.history.append({"role": "user", "content": message})

        if use_llm and llm_client is not None:
            updates = self._extract_with_llm(message, llm_client)
            self._merge_updates(updates)

        rule_updates = self._extract_with_rules(message)
        self._merge_updates(rule_updates)

    def _extract_with_llm(self, message, llm_client):
        prompt = f"""
Extract a Bangalore home buyer profile from the message.
Return only valid JSON. Use null for unknown values.

Schema:
{{
  "budget": number | null,
  "bhk": number | null,
  "property_type": "Apartment" | "Villa" | "Plot" | null,
  "preferred_locations": string[],
  "office": string | null,
  "family_size": number | null,
  "school_priority": boolean | null,
  "metro_priority": boolean | null,
  "investment_priority": boolean | null,
  "pet_friendly": boolean | null,
  "ready_to_move": boolean | null,
  "lifestyle": string[],
  "amenities": string[]
}}

Message: {message}
"""
        try:
            response = llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            content = response.choices[0].message.content.strip()
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            return {}
        return {}

    def _extract_with_rules(self, message):
        text = message.lower()
        updates = {
            "preferred_locations": [],
            "lifestyle": [],
            "amenities": [],
        }

        budget = self._extract_budget(text)
        if budget:
            updates["budget"] = budget

        bhk = self._extract_bhk(text)
        if bhk:
            updates["bhk"] = bhk

        property_type = self._extract_property_type(text)
        if property_type:
            updates["property_type"] = property_type

        location_updates = self._extract_locations(text)
        updates["preferred_locations"].extend(location_updates["preferred_locations"])
        if location_updates.get("office"):
            updates["office"] = location_updates["office"]

        family_size = self._extract_family(text)
        if family_size:
            updates["family_size"] = family_size

        updates.update(self._extract_priorities(text))
        updates["lifestyle"].extend(self._extract_lifestyle(text))
        updates["amenities"].extend(self._extract_amenities(text))
        return updates

    def _merge_updates(self, updates):
        if not isinstance(updates, dict):
            return

        list_fields = {"preferred_locations", "lifestyle", "amenities"}
        for field, value in updates.items():
            if field not in self.profile or value in (None, "", [], {}):
                continue

            if field in list_fields:
                values = value if isinstance(value, list) else [value]
                for item in values:
                    label = self._normalise_label(item)
                    if label and label not in self.profile[field]:
                        self.profile[field].append(label)
                continue

            if isinstance(self.profile[field], bool) and value is None:
                continue

            self.profile[field] = value

    def _normalise_label(self, value):
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        area_lookup = {area: area.title() for area in KNOWN_AREAS}
        return area_lookup.get(text.lower(), text.title())

    def _extract_budget(self, text):
        crore = re.search(
            r"(?:under|below|upto|up to|around|budget is|budget of|max|maximum)?\s*(\d+(?:\.\d+)?)\s*(crore|crores|cr)",
            text,
        )
        lakh = re.search(
            r"(?:under|below|upto|up to|around|budget is|budget of|max|maximum)?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l)",
            text,
        )

        if crore:
            return int(float(crore.group(1)) * 10_000_000)
        if lakh:
            return int(float(lakh.group(1)) * 100_000)
        return None

    def _extract_bhk(self, text):
        match = re.search(r"(\d+)\s*(bhk|bed|beds|bedroom|bedrooms)", text)
        return int(match.group(1)) if match else None

    def _extract_property_type(self, text):
        if any(word in text for word in ["apartment", "flat", "condo"]):
            return "Apartment"
        if any(word in text for word in ["villa", "independent house", "house"]):
            return "Villa"
        if any(word in text for word in ["plot", "land"]):
            return "Plot"
        return None

    def _extract_locations(self, text):
        updates = {"preferred_locations": [], "office": None}
        for area in KNOWN_AREAS:
            if area not in text:
                continue

            label = area.title()
            updates["preferred_locations"].append(label)

            office_patterns = [
                f"work in {area}",
                f"working in {area}",
                f"office in {area}",
                f"near my office in {area}",
                f"commute to {area}",
                f"work at {area}",
            ]
            if any(pattern in text for pattern in office_patterns):
                updates["office"] = label
        return updates

    def _extract_family(self, text):
        family = re.search(r"(family of|we are|household of)\s*(\d+)", text)
        if family:
            return int(family.group(2))

        kids = re.search(r"(\d+)\s*(kids|children|child)", text)
        if kids:
            return int(kids.group(1)) + 2

        if any(word in text for word in ["kids", "children", "parents"]):
            return self.profile.get("family_size")
        return None

    def _extract_priorities(self, text):
        updates = {}

        if any(phrase in text for phrase in ["schools do not matter", "school does not matter", "no school preference"]):
            updates["school_priority"] = False
        elif any(word in text for word in ["school", "schools", "kid", "children"]):
            updates["school_priority"] = True

        if any(phrase in text for phrase in ["metro not important", "no metro"]):
            updates["metro_priority"] = False
        elif any(word in text for word in ["metro", "station", "public transport"]):
            updates["metro_priority"] = True

        if any(word in text for word in ["investment", "roi", "appreciation", "rental", "return"]):
            updates["investment_priority"] = True

        if any(phrase in text for phrase in ["no pets", "not pet"]):
            updates["pet_friendly"] = False
        elif any(word in text for word in ["pet", "dog", "cat"]):
            updates["pet_friendly"] = True

        if "ready to move" in text or "ready-to-move" in text:
            updates["ready_to_move"] = True
        return updates

    def _extract_lifestyle(self, text):
        options = {
            "quiet": ["quiet", "peaceful", "calm"],
            "family friendly": ["family friendly", "kids", "children"],
            "premium": ["premium", "luxury", "upscale"],
            "walkable": ["walkable", "walking"],
            "green": ["green", "parks", "garden"],
            "nightlife": ["nightlife", "cafes", "restaurants"],
            "gated community": ["gated", "security"],
        }
        return [label for label, words in options.items() if any(word in text for word in words)]

    def _extract_amenities(self, text):
        options = {
            "Gym": ["gym", "fitness"],
            "Pool": ["pool", "swimming"],
            "Club House": ["club house", "clubhouse"],
            "Parking": ["parking", "car park"],
            "Kids Play Area": ["kids play", "play area"],
            "Security": ["security", "gated"],
            "Garden": ["garden", "park"],
        }
        return [label for label, words in options.items() if any(word in text for word in words)]

    def missing_fields(self):
        missing = []
        if self.profile["budget"] is None:
            missing.append("budget")
        if self.profile["bhk"] is None:
            missing.append("bhk")
        if self.profile["property_type"] is None:
            missing.append("property_type")
        if not self.profile["preferred_locations"] and self.profile["office"] is None:
            missing.append("location")
        return missing

    def ready_to_search(self):
        return len(self.missing_fields()) == 0

    def profile_completion(self):
        tracked = [
            "budget",
            "bhk",
            "property_type",
            "preferred_locations",
            "office",
            "family_size",
            "school_priority",
            "metro_priority",
            "investment_priority",
            "pet_friendly",
            "lifestyle",
        ]
        filled = 0
        for field in tracked:
            value = self.profile.get(field)
            if value not in (None, False, [], {}):
                filled += 1
        return round((filled / len(tracked)) * 100)

    def next_question(self):
        questions = {
            "budget": "What budget should I stay within?",
            "bhk": "How many BHK do you need?",
            "property_type": "Are you looking for an apartment, villa, or plot?",
            "location": "Which Bangalore locality should I focus on?",
        }
        missing = self.missing_fields()
        if not missing:
            return None

        for field in missing:
            if field not in self.asked_fields:
                self.asked_fields.add(field)
                return questions[field]

        labels = ", ".join(questions[field].rstrip("?").lower() for field in missing)
        return f"I still need this to search properly: {labels}."
