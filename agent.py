from config import client
from conversation import ConversationManager
from executor import ToolExecutor
from planner import AIPlanner
from ranking import RankingEngine


class HomeFinderAgent:
    """Coordinates memory, planning, execution, ranking, and explanation."""

    def __init__(self, llm_client=client):
        self.llm_client = llm_client
        self.conversation = ConversationManager()
        self.planner = AIPlanner()
        self.executor = ToolExecutor()
        self.ranking = RankingEngine()

    def reset(self):
        self.conversation.reset_profile()

    def run(self, user_message, use_llm_extraction=True):
        self.conversation.update_profile(
            user_message,
            llm_client=self.llm_client,
            use_llm=use_llm_extraction,
        )
        buyer = self.conversation.get_profile()

        if not self.conversation.ready_to_search():
            message = self.conversation.next_question()
            self.conversation.record_assistant(message)
            return {
                "type": "question",
                "message": message,
                "profile": buyer,
                "profile_completion": self.conversation.profile_completion(),
                "memory": self.conversation.get_memory_snapshot(),
            }

        plan = self.planner.create_plan(buyer)
        plan_details = self.planner.create_plan_details(buyer)
        results = self.executor.execute(plan, buyer)
        ranked = self.ranking.rank(results, buyer)
        self._attach_property_summaries(ranked, buyer)

        explanation = self._build_explanation(buyer, ranked, plan_details)
        self.conversation.record_assistant(explanation)

        return {
            "type": "recommendation",
            "buyer": buyer,
            "plan": plan,
            "plan_details": plan_details,
            "results": ranked,
            "explanation": explanation,
            "profile_completion": self.conversation.profile_completion(),
            "memory": self.conversation.get_memory_snapshot(),
            "tool_errors": results.get("errors", []),
            "search_notes": results.get("search_notes", []),
        }

    def _attach_property_summaries(self, ranked, buyer):
        for item in ranked:
            prop = item["property"]
            strengths = ", ".join(item.get("pros", [])[:3]) or "good overall fit"
            tradeoffs = ", ".join(item.get("tradeoffs", [])[:2]) or "few visible trade-offs"
            item["ai_summary"] = (
                f"{prop['name']} is a {item['match']} match because of {strengths}. "
                f"Watch for {tradeoffs}."
            )

    def _build_explanation(self, buyer, ranked, plan_details):
        if not ranked:
            return (
                "I could not find a strong match with the current constraints. "
                "The best next move is to widen the locality, relax BHK, or increase budget flexibility."
            )

        deterministic = self._fallback_explanation(buyer, ranked, plan_details)
        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": self._explanation_prompt(buyer, ranked, plan_details),
                    }
                ],
                temperature=0.4,
            )
            content = response.choices[0].message.content.strip()
            return content or deterministic
        except Exception:
            return deterministic

    def _explanation_prompt(self, buyer, ranked, plan_details):
        property_lines = []
        for index, item in enumerate(ranked[:5], start=1):
            prop = item["property"]
            property_lines.append(
                {
                    "rank": index,
                    "name": prop["name"],
                    "location": prop["location"],
                    "price": prop["price"],
                    "score": item["score"],
                    "confidence": item["confidence"],
                    "pros": item.get("pros", []),
                    "cons": item.get("cons", []),
                    "tradeoffs": item.get("tradeoffs", []),
                    "roi": prop.get("roi"),
                    "growth": prop.get("price_growth"),
                }
            )

        return f"""
You are HomeFinder AI, a concise real estate consultant.

Buyer profile:
{buyer}

Execution plan:
{plan_details}

Ranked properties:
{property_lines}

Write a recommendation that covers:
- why the top property was selected
- why lower ranked properties are weaker or rejected
- strengths, weaknesses, and trade-offs
- investment potential and future appreciation
Keep it polished, specific, and buyer-facing.
"""

    def _fallback_explanation(self, buyer, ranked, plan_details):
        best = ranked[0]
        prop = best["property"]
        lines = [
            f"My strongest recommendation is {prop['name']} in {prop['location']} with a {best['match']} match and {best['confidence']}% confidence.",
            f"Why selected: {', '.join(best.get('pros', [])[:4]) or 'it fits the core profile.'}",
        ]

        if best.get("tradeoffs"):
            lines.append(f"Trade-offs: {', '.join(best['tradeoffs'][:3])}.")
        if best.get("cons"):
            lines.append(f"Weaknesses: {', '.join(best['cons'][:3])}.")

        investment = []
        if prop.get("roi") is not None:
            investment.append(f"{prop['roi']}% ROI")
        if prop.get("price_growth") is not None:
            investment.append(f"{prop['price_growth']}% price growth")
        if investment:
            lines.append(f"Investment potential: {', '.join(investment)}.")

        if len(ranked) > 1:
            rejected = []
            for item in ranked[1:4]:
                p = item["property"]
                reason = ", ".join((item.get("cons") or item.get("tradeoffs") or ["lower total fit"])[:2])
                rejected.append(f"{p['name']} ranks lower because {reason}")
            lines.append("Why others rank lower: " + "; ".join(rejected) + ".")

        tools = ", ".join(detail["tool"] for detail in plan_details)
        lines.append(f"I used these tools: {tools}.")
        return "\n\n".join(lines)


default_agent = HomeFinderAgent()


def run_agent(user_message, agent=None, conversation_manager=None, use_llm_extraction=True):
    """Compatibility wrapper for existing scripts and tests."""

    if agent is not None:
        return agent.run(user_message, use_llm_extraction=use_llm_extraction)

    if conversation_manager is not None:
        scoped_agent = HomeFinderAgent()
        scoped_agent.conversation = conversation_manager
        return scoped_agent.run(user_message, use_llm_extraction=use_llm_extraction)

    return default_agent.run(user_message, use_llm_extraction=use_llm_extraction)
