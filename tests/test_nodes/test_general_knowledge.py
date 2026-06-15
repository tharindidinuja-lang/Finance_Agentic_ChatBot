import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from unittest.mock import patch

from nodes.planner_node import planner_node
from nodes.response_generation_node import generate_normal_response
from state.finance_state import create_initial_state


class TestGeneralKnowledgeFallback(unittest.TestCase):
    def setUp(self):
        self.user_id = "test_user_001"

    def create_state(self, user_message: str):
        state = create_initial_state(self.user_id)
        state["messages"].append({"role": "user", "content": user_message})
        state["current_plan"] = ["general_query"]
        return state

    @patch("nodes.planner_node.ChatOpenAI.invoke", side_effect=RuntimeError("401 Unauthorized"))
    def test_planner_fallback_does_not_use_transaction_history(self, _mock_invoke):
        state = self.create_state("What is an ETF?")

        result = planner_node(state)

        self.assertEqual(result["current_plan"], [])

    def test_general_query_response_uses_fallback_explanation(self):
        state = self.create_state("What is an ETF?")
        state["tool_results"] = []

        response = generate_normal_response(state)

        self.assertIn("ETF", response)
        self.assertNotIn("recent transactions", response.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
