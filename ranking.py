class RankingEngine:
    """Weighted scoring engine for buyer-property fit."""

    def calculate_score(self, item, buyer):
        prop = item["property"]
        score = 0
        pros = []
        cons = []
        tradeoffs = []

        score += self._budget_score(item, pros, cons)
        score += self._rating_score(prop, pros)
        score += self._commute_score(item, buyer, pros, cons, tradeoffs)
        score += self._school_score(item, buyer, pros, tradeoffs)
        score += self._metro_score(item, buyer, pros, tradeoffs)
        score += self._safety_score(item, prop, pros, tradeoffs)
        score += self._investment_score(item, prop, buyer, pros, tradeoffs)
        score += self._amenity_score(prop, buyer, pros)

        score = min(100, round(score))
        reasons = pros[:5] if pros else ["Matches the available buyer profile."]
        return score, reasons, pros, cons, tradeoffs

    def _budget_score(self, item, pros, cons):
        affordability = item.get("affordability", {})
        if affordability.get("affordable"):
            remaining = affordability.get("remaining_budget", 0)
            if remaining >= 500_000:
                pros.append("Comfortably within budget")
                return 25
            pros.append("Within budget")
            return 20

        cons.append("Above the stated budget")
        return 0

    def _rating_score(self, prop, pros):
        rating = prop.get("rating", 0)
        points = min(15, rating * 3)
        if rating >= 4.7:
            pros.append("Top-tier resident rating")
        elif rating >= 4.4:
            pros.append("Strong resident rating")
        return points

    def _commute_score(self, item, buyer, pros, cons, tradeoffs):
        if not buyer.get("office"):
            return 0

        commute = item.get("commute", {})
        try:
            minutes = int(commute.get("time_min", 999))
        except (TypeError, ValueError):
            minutes = 999

        if minutes <= 20:
            pros.append("Excellent office commute")
            return 15
        if minutes <= 40:
            pros.append("Practical office commute")
            return 10
        if minutes < 999:
            tradeoffs.append("Commute is manageable but not ideal")
            return 4

        cons.append("Commute data is unavailable")
        return 0

    def _school_score(self, item, buyer, pros, tradeoffs):
        if not buyer.get("school_priority"):
            return 0

        schools = item.get("schools", [])
        property_rating = item["property"].get("school_rating", 0)
        if len(schools) >= 2 or property_rating >= 9:
            pros.append("Strong school access")
            return 15
        if schools or property_rating >= 8:
            tradeoffs.append("School access is acceptable but not best-in-class")
            return 9
        return 0

    def _metro_score(self, item, buyer, pros, tradeoffs):
        if not buyer.get("metro_priority"):
            return 0

        prop = item["property"]
        neighbourhood = item.get("neighbourhood", {})
        distance = prop.get("metro_distance", 99999)
        has_metro = neighbourhood.get("metro")

        if has_metro or distance <= 500:
            pros.append("Convenient metro access")
            return 10
        if distance <= 800:
            tradeoffs.append("Metro is nearby, but not walking-close")
            return 6
        return 0

    def _safety_score(self, item, prop, pros, tradeoffs):
        neighbourhood = item.get("neighbourhood", {})
        safety = neighbourhood.get("safety", prop.get("crime_score", 0))
        try:
            safety = float(safety)
        except (TypeError, ValueError):
            safety = 0

        if safety >= 8.8:
            pros.append("High safety signal")
            return 10
        if safety >= 8:
            tradeoffs.append("Safety signal is solid")
            return 7
        return 0

    def _investment_score(self, item, prop, buyer, pros, tradeoffs):
        if not buyer.get("investment_priority"):
            return 0

        roi = prop.get("roi", 0)
        growth = prop.get("price_growth", 0)
        history = item.get("price_history", [])

        appreciating = bool(history and history[-1] > history[0])
        if roi >= 18 or growth >= 16 or appreciating:
            pros.append("Strong investment and appreciation signal")
            return 15
        if roi >= 15 or growth >= 12:
            tradeoffs.append("Investment outlook is positive but moderate")
            return 9
        return 0

    def _amenity_score(self, prop, buyer, pros):
        amenities = prop.get("amenities", [])
        score = min(10, len(amenities) * 2)
        if buyer.get("pet_friendly") and prop.get("pet_friendly"):
            score += 3
            pros.append("Pet-friendly community")
        if len(amenities) >= 4:
            pros.append("Rich amenity mix")
        return min(12, score)

    def rank(self, results, buyer):
        ranked = []
        properties = results.get("properties", [])

        for item in properties:
            score, reasons, pros, cons, tradeoffs = self.calculate_score(item, buyer)
            evidence_count = len(item.get("tools_used", []))
            profile_fields = [
                buyer.get("budget"),
                buyer.get("bhk"),
                buyer.get("property_type"),
                buyer.get("office"),
            ]
            profile_strength = sum(1 for value in profile_fields if value) * 5

            item["score"] = score
            item["match"] = f"{score}%"
            item["confidence"] = min(98, 58 + profile_strength + evidence_count * 4 + score // 5)
            item["reason"] = reasons
            item["pros"] = pros
            item["cons"] = cons
            item["tradeoffs"] = tradeoffs
            ranked.append(item)

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
