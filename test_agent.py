import unittest

from agent import HomeFinderAgent


class _FailingCompletion:
    def create(self, *args, **kwargs):
        raise RuntimeError("LLM disabled for unit tests")


class _FailingChat:
    completions = _FailingCompletion()


class _FakeLLM:
    chat = _FailingChat()


class AgentFlowTests(unittest.TestCase):
    def test_agent_uses_memory_across_turns(self):
        agent = HomeFinderAgent(llm_client=_FakeLLM())

        first = agent.run("I want an apartment", use_llm_extraction=False)
        self.assertEqual(first["type"], "question")
        self.assertEqual(first["message"], "What budget should I stay within?")

        second = agent.run("Budget is 90 lakh", use_llm_extraction=False)
        self.assertEqual(second["type"], "question")
        self.assertEqual(second["message"], "How many BHK do you need?")

        final = agent.run(
            "3 BHK in Electronic City. I work in Electronic City. "
            "Schools, metro, investment and pets matter.",
            use_llm_extraction=False,
        )

        self.assertEqual(final["type"], "recommendation")
        self.assertGreaterEqual(len(final["results"]), 1)
        self.assertIn("property_search", final["plan"])
        self.assertIn("estimate_commute", final["plan"])
        self.assertEqual(final["buyer"]["budget"], 9_000_000)
        self.assertEqual(final["buyer"]["bhk"], 3)
        self.assertEqual(final["buyer"]["property_type"], "Apartment")
        self.assertIn("Electronic City", final["buyer"]["preferred_locations"])
        self.assertGreaterEqual(final["profile_completion"], 70)

    def test_agent_returns_follow_up_for_missing_search_fields(self):
        agent = HomeFinderAgent(llm_client=_FakeLLM())

        result = agent.run("I want a quiet family friendly home", use_llm_extraction=False)

        self.assertEqual(result["type"], "question")
        self.assertIn("budget", result["message"].lower())
        self.assertIn("asked_fields", result["memory"])


if __name__ == "__main__":
    unittest.main()
