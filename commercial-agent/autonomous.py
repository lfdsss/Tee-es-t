"""Autonomous Commercial Agent — runs unattended on a schedule.

This script performs a full morning routine:
1. Check unread emails → identify real prospects → draft responses
2. Check HubSpot tasks due today
3. Follow up on stale prospects
4. Log activity summary
"""

import os
import logging
from datetime import datetime

from dotenv import load_dotenv

from config.routines import ROUTINES
from agent_loop import run_agent_loop
from config.system_prompt import get_system_prompt
from tools import ALL_TOOLS, execute_tool

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("commercial-agent")


def run_autonomous(routine: str) -> str:
    """Run an autonomous routine via the shared agent loop."""
    if routine not in ROUTINES:
        log.error(f"Unknown routine: {routine}. Available: {list(ROUTINES.keys())}")
        return f"Error: unknown routine '{routine}'"

    log.info(f"Starting routine: {routine}")

    result = run_agent_loop(
        user_prompt=ROUTINES[routine],
        system_prompt=get_system_prompt(),
        tools=ALL_TOOLS,
        execute_tool=execute_tool,
        max_iterations=25,
        on_text=lambda text: log.info(f"  Agent: {text[:200]}"),
    )

    log.info(f"Routine '{routine}' result:\n{result[:500]}")
    return result


def main():
    """Entry point — determines which routine to run based on args or time."""
    import sys

    if len(sys.argv) > 1:
        routine = sys.argv[1]
    else:
        # Auto-select based on time of day
        hour = datetime.now().hour
        weekday = datetime.now().weekday()

        if weekday == 4 and hour >= 16:  # Friday afternoon
            routine = "weekly_audit"
        elif hour < 12:
            routine = "morning"
        else:
            routine = "followup"

    log.info(f"=== AUTONOMOUS AGENT — {routine.upper()} — {datetime.now().isoformat()} ===")
    result = run_autonomous(routine)

    # Save report
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(
        report_dir,
        f"{routine}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
    )
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"=== {routine.upper()} — {datetime.now().isoformat()} ===\n\n")
        f.write(result)

    log.info(f"Report saved: {report_file}")


if __name__ == "__main__":
    main()
