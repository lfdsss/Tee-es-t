"""Smoke tests for the commercial-agent.

Goal: catch import errors and tool-routing regressions *before* the
cron-triggered prod run fails silently. These tests intentionally avoid any
real network I/O — they only validate the static structure of the app:

  - Tools package imports cleanly and exposes ALL_TOOLS.
  - Each tool entry has the Anthropic-API shape (name, description, input_schema).
  - execute_tool() dispatches by prefix to the right handler and returns a
    string for unknown tools (not a crash).
  - config.system_prompt.get_system_prompt() returns a non-empty string.
  - autonomous.ROUTINES exists and contains the well-known routine keys that
    the Railway cron / GitHub Actions scheduler rely on.
"""

from __future__ import annotations

from unittest.mock import patch


def test_tools_package_imports() -> None:
    import tools

    assert hasattr(tools, "ALL_TOOLS")
    assert isinstance(tools.ALL_TOOLS, list)
    assert len(tools.ALL_TOOLS) > 0


def test_all_tools_have_anthropic_shape() -> None:
    import tools

    for entry in tools.ALL_TOOLS:
        assert isinstance(entry, dict), f"Tool entry is not a dict: {entry!r}"
        assert "name" in entry and isinstance(entry["name"], str) and entry["name"]
        assert "description" in entry and isinstance(entry["description"], str)
        assert "input_schema" in entry and isinstance(entry["input_schema"], dict)


def test_tool_name_prefixes_are_known() -> None:
    """Every registered tool must use a prefix execute_tool() can route."""
    import tools

    known_prefixes = ("hubspot_", "gmail_", "notion_", "github_", "livrables_", "laposte_")
    for entry in tools.ALL_TOOLS:
        name = entry["name"]
        assert name.startswith(known_prefixes), f"Unrouted tool prefix: {name}"


def test_execute_tool_unknown_name_returns_error_string() -> None:
    from tools import execute_tool

    result = execute_tool("totally_unknown_tool", {})
    assert isinstance(result, str)
    assert "Unknown tool" in result


def test_execute_tool_routes_by_prefix() -> None:
    """Ensure the dispatcher calls the correct sub-handler based on prefix."""
    import tools as tools_pkg

    with patch.object(tools_pkg, "execute_hubspot_tool", return_value="HUBSPOT_OK") as hs:
        assert tools_pkg.execute_tool("hubspot_search_contacts", {"q": "x"}) == "HUBSPOT_OK"
        hs.assert_called_once()

    with patch.object(tools_pkg, "execute_notion_tool", return_value="NOTION_OK") as no:
        assert tools_pkg.execute_tool("notion_create_page", {}) == "NOTION_OK"
        no.assert_called_once()

    with patch.object(tools_pkg, "execute_github_tool", return_value="GH_OK") as gh:
        assert tools_pkg.execute_tool("github_list_issues", {}) == "GH_OK"
        gh.assert_called_once()

    with patch.object(tools_pkg, "execute_livrables_tool", return_value="LV_OK") as lv:
        assert tools_pkg.execute_tool("livrables_create_devis", {}) == "LV_OK"
        lv.assert_called_once()


def test_system_prompt_returns_non_empty_string() -> None:
    from config.system_prompt import get_system_prompt

    prompt = get_system_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 100  # sanity: should be a substantial persona prompt


def test_routines_contains_expected_keys() -> None:
    """Routines live in a dependency-free module so schedulers/tests can
    import them without pulling the anthropic SDK."""
    from config.routines import ROUTINES

    assert isinstance(ROUTINES, dict)
    # These three keys are referenced by schedulers (Railway cron / workflows).
    for key in ("morning", "followup", "weekly_audit"):
        assert key in ROUTINES, f"Missing routine: {key}"
        assert ROUTINES[key].strip(), f"Empty routine body: {key}"


def test_laposte_track_and_notify_detects_only_changes(tmp_path) -> None:
    """The notification engine must emit a shipment only when its status changed
    vs the persisted state — and persist the new state for the next run."""
    from unittest.mock import patch

    from tools import laposte

    state = tmp_path / "state.json"
    fake = {
        "tracking_number": "07461145240",
        "found": True,
        "is_final": False,
        "current_status": "Pris en charge.",
        "current_status_date": "2026-05-28T09:00:00+02:00",
        "carrier": "La Poste",
        "tracking_url": "https://example/track",
    }

    notified: list[str] = []
    with patch.object(laposte, "track_shipment", return_value=fake):
        # First run → new code, must be reported once.
        res1 = laposte.track_and_notify(
            ["07461145240"], state_path=str(state), sink=notified.append
        )
        assert res1["changed_count"] == 1
        assert len(notified) == 1

        # Second run, same status → no change, nothing emitted.
        res2 = laposte.track_and_notify(
            ["07461145240"], state_path=str(state), sink=notified.append
        )
        assert res2["changed_count"] == 0
        assert len(notified) == 1

    # Status changes (delivered) → reported again.
    delivered = dict(fake, is_final=True, current_status="Votre courrier a ete distribue.")
    with patch.object(laposte, "track_shipment", return_value=delivered):
        res3 = laposte.track_and_notify(
            ["07461145240"], state_path=str(state), sink=notified.append
        )
        assert res3["changed_count"] == 1
        assert len(notified) == 2


def test_laposte_load_state_tolerates_missing_and_corrupt(tmp_path) -> None:
    from tools import laposte

    missing = tmp_path / "nope.json"
    assert laposte._load_state(str(missing)) == {}

    corrupt = tmp_path / "bad.json"
    corrupt.write_text("{not valid json", encoding="utf-8")
    assert laposte._load_state(str(corrupt)) == {}
