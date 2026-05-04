"""Commercial Agent - L-FDS

Interactive entry point for the commercial agent. The actual agentic
loop lives in `agent_loop.py` and is shared with `autonomous.py` (the
cron entry point). This file just wires a REPL around it.
"""

from dotenv import load_dotenv

from agent_loop import run_agent_loop
from config.system_prompt import get_system_prompt
from tools import ALL_TOOLS, execute_tool

load_dotenv()


def run_agent(user_message: str) -> str:
    """Run the commercial agent with a user message."""
    print(f"\n{'='*60}")
    print("AGENT COMMERCIAL - Traitement de la demande...")
    print(f"{'='*60}\n")

    return run_agent_loop(
        user_prompt=user_message,
        system_prompt=get_system_prompt(),
        tools=ALL_TOOLS,
        execute_tool=execute_tool,
        max_iterations=15,
        on_text=lambda text: print(f"[Agent] {text[:200]}"),
    )


def interactive_mode():
    """Run the agent in interactive mode (chat loop)."""
    print("\n" + "=" * 60)
    print("  AGENT COMMERCIAL L-FDS")
    print("  Tape 'quit' pour quitter")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n[Baptiste] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Au revoir!")
            break

        result = run_agent(user_input)
        print(f"\n[Agent Commercial]\n{result}")


if __name__ == "__main__":
    interactive_mode()
