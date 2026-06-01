import logging

# Always available
from .github_tools import GITHUB_TOOLS, execute_github_tool
from .hubspot import HUBSPOT_TOOLS, execute_hubspot_tool
from .laposte import LAPOSTE_TOOLS, execute_laposte_tool
from .livrables import LIVRABLES_TOOLS, execute_livrables_tool
from .notion import NOTION_TOOLS, execute_notion_tool

log = logging.getLogger("commercial-agent")

ALL_TOOLS = HUBSPOT_TOOLS + NOTION_TOOLS + GITHUB_TOOLS + LIVRABLES_TOOLS + LAPOSTE_TOOLS

# Gmail is optional (requires OAuth flow with browser on first use).
# Broad except is intentional: any import-time failure (missing deps, bad
# credentials, OAuth issue) must downgrade gracefully — never crash the agent.
try:
    from .gmail import GMAIL_AVAILABLE, GMAIL_TOOLS, execute_gmail_tool
    if GMAIL_AVAILABLE:
        ALL_TOOLS = ALL_TOOLS + GMAIL_TOOLS
        log.info(f"Gmail tools loaded ({len(GMAIL_TOOLS)} tools)")
    else:
        log.warning("Gmail dependencies not installed — Gmail tools disabled")
        execute_gmail_tool = None
except Exception as e:
    log.warning(f"Gmail tools not available: {e}")
    GMAIL_TOOLS = []
    execute_gmail_tool = None


def execute_tool(name: str, input_data: dict) -> str:
    """Route tool execution to the right handler."""
    if name.startswith("hubspot_"):
        return execute_hubspot_tool(name, input_data)
    elif name.startswith("gmail_"):
        if execute_gmail_tool is None:
            return "Error: Gmail is not configured. Run the agent locally first with 'python main.py' to complete the OAuth flow, then redeploy."
        return execute_gmail_tool(name, input_data)
    elif name.startswith("notion_"):
        return execute_notion_tool(name, input_data)
    elif name.startswith("github_"):
        return execute_github_tool(name, input_data)
    elif name.startswith("livrables_"):
        return execute_livrables_tool(name, input_data)
    elif name.startswith("laposte_"):
        return execute_laposte_tool(name, input_data)
    else:
        return f"Error: Unknown tool '{name}'"
