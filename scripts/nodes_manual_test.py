import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import logging
logging.basicConfig(level=logging.INFO)

from app.nodes import scrape_node, summarize_node, save_node, error_node

if __name__ == "__main__":
    print("=== Running scrape_node ===")
    state = {}
    state.update(scrape_node(state))

    if state.get("error"):
        print(f"scrape_node reported an error: {state['error']}")
        error_node(state)
        sys.exit(1)

    print(f"scrape_node OK — {len(state['emails'])} emails in state\n")

    print("=== Running summarize_node ===")
    state.update(summarize_node(state))

    if state.get("error"):
        print(f"summarize_node reported an error: {state['error']}")
        error_node(state)
        sys.exit(1)

    print(f"summarize_node OK — {len(state['digest_items'])} digest items in state\n")

    print("=== Running save_node ===")
    state.update(save_node(state))

    if state.get("error"):
        print(f"save_node reported an error: {state['error']}")
        error_node(state)
        sys.exit(1)

    print(f"save_node OK — digest saved to {state['output_path']}\n")

    print("=== Full pipeline succeeded ===")
    print(f"Final state keys: {list(state.keys())}")