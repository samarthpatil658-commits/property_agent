import unittest

from config import client


class ConfigTests(unittest.TestCase):
    def test_groq_client_is_configured_object(self):
        self.assertIsNotNone(client)
        self.assertTrue(hasattr(client, "chat"))


if __name__ == "__main__":
    unittest.main()
