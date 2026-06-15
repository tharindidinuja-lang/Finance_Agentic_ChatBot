import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from state.finance_state import create_initial_state
from workflows.finance_graph import create_finance_graph
from utils.message_utils import get_message_role, get_message_content

app = create_finance_graph()

queries = [
    "What's the Apple stock price?",
    "What is my current balance?",
    "What is an ETF?",
]

for q in queries:
    state = create_initial_state('test_user_001')
    state['messages'].append({'role': 'user', 'content': q})
    result = app.invoke(state)

    msgs = result.get('messages', [])
    assistant = [m for m in msgs if get_message_role(m) == 'assistant']

    print(f"\nQ: {q}")
    print(f"  Intent  : {result.get('intent')}")
    print(f"  Plan    : {result.get('current_plan')}")
    tools = [(r.get('tool_name'), r.get('status')) for r in result.get('tool_results', [])]
    print(f"  Tools   : {tools}")
    print(f"  Response: {get_message_content(assistant[0]) if assistant else '(no response)'}")
