"""Shared agentic loop for the Commercial Agent.

Both `main.py` (interactive) and `autonomous.py` (cron) go through
`run_agent_loop`. Centralising the loop here gets us:

- **Prompt caching** on the system prompt via `cache_control: ephemeral`.
  The system prompt + tool definitions are rendered once at the prefix of
  every request in a routine, so cache hits from iteration 2 onward cut
  input-token cost by ~90% for the cached portion. Verified via
  `response.usage.cache_read_input_tokens` in the debug log.

- **Typed exception handling** — rate limits get exponential backoff +
  retry (up to 3 attempts), other `APIError`s abort cleanly with an
  actionable log line instead of swallowing every `Exception` as a string.

- **One implementation** — previously `main.py` and `autonomous.py` each
  carried a near-identical ~50-line loop with drift risk. Now they're
  thin entry points that call this module.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Iterable

import anthropic

log = logging.getLogger("commercial-agent")

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_MAX_TOKENS = 16000
TOOL_RESULT_TRUNCATE_AT = 5000
RATE_LIMIT_MAX_RETRIES = 3


def _cached_system(system_prompt: str) -> list[dict]:
    """Render the system prompt as a cacheable content block.

    The `cache_control: ephemeral` marker on the last system block causes
    the API to cache everything rendered up to that point — tools first,
    then system — for 5 minutes. Subsequent iterations in the same routine
    hit the cache at ~0.1x the base input price.
    """
    return [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def _call_with_retries(
    client: anthropic.Anthropic,
    *,
    model: str,
    max_tokens: int,
    system: list[dict],
    tools: list,
    messages: list,
) -> anthropic.types.Message:
    """Call `messages.create` with exponential backoff on rate limits.

    Rate-limit errors are retryable — back off 2s, 4s, 8s. Any other
    `APIError` (auth, bad request, server error) is re-raised so the
    caller can log and abort. We deliberately don't retry 5xx here
    because the SDK already does that under the hood (`max_retries=2`).
    """
    attempt = 0
    while True:
        try:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                tools=tools,
                messages=messages,
            )
        except anthropic.RateLimitError as e:
            attempt += 1
            if attempt > RATE_LIMIT_MAX_RETRIES:
                log.error(f"  Rate limit exhausted after {attempt} attempts: {e}")
                raise
            delay = 2**attempt
            log.warning(
                f"  Rate limited (attempt {attempt}/{RATE_LIMIT_MAX_RETRIES}), "
                f"sleeping {delay}s"
            )
            time.sleep(delay)


def run_agent_loop(
    *,
    user_prompt: str,
    system_prompt: str,
    tools: Iterable[dict],
    execute_tool: Callable[[str, dict], str],
    max_iterations: int = 25,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    client: anthropic.Anthropic | None = None,
    on_text: Callable[[str], None] | None = None,
) -> str:
    """Run the commercial agent loop until `end_turn` or `max_iterations`.

    Parameters
    ----------
    user_prompt:
        Initial user message — a routine definition or an interactive
        question.
    system_prompt:
        Agent persona / operating instructions. Cached via `cache_control`.
    tools:
        Tool definitions in Anthropic API shape.
    execute_tool:
        Callback that routes a tool call to the right handler and returns
        a string result. Tool execution errors are caught here and fed
        back to the model as `is_error: true` tool results, so the model
        can adapt rather than crash the routine.
    max_iterations:
        Safety cap on the loop. 25 is enough for the longest routines
        (`weekly_audit`) observed in production.
    model, max_tokens:
        Forwarded to `messages.create`.
    client:
        Optional injected `anthropic.Anthropic` instance — useful for
        testing. Defaults to a fresh client which reads `ANTHROPIC_API_KEY`
        from the env.
    on_text:
        Optional callback invoked for each non-empty assistant text block
        between iterations. Used by `main.py` for interactive streaming
        and by `autonomous.py` for log output.

    Returns
    -------
    The final text returned when the model signals `stop_reason == "end_turn"`,
    or a short error message on API / iteration-cap failure.
    """
    client = client or anthropic.Anthropic()
    tools = list(tools)
    system = _cached_system(system_prompt)
    messages: list[dict] = [{"role": "user", "content": user_prompt}]

    for iteration in range(1, max_iterations + 1):
        log.info(f"  Iteration {iteration}/{max_iterations}")

        try:
            response = _call_with_retries(
                client,
                model=model,
                max_tokens=max_tokens,
                system=system,
                tools=tools,
                messages=messages,
            )
        except anthropic.AuthenticationError as e:
            log.error(f"  Auth error — check ANTHROPIC_API_KEY: {e}")
            return f"API Error (auth): {e}"
        except anthropic.BadRequestError as e:
            log.error(f"  Bad request — likely a schema or message shape bug: {e}")
            return f"API Error (bad request): {e}"
        except anthropic.APIError as e:
            log.error(f"  API error: {e}")
            return f"API Error: {e}"

        usage = getattr(response, "usage", None)
        if usage is not None:
            log.info(
                f"  tokens: in={usage.input_tokens} "
                f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)} "
                f"cache_create={getattr(usage, 'cache_creation_input_tokens', 0)} "
                f"out={usage.output_tokens}"
            )

        text_blocks = [b for b in response.content if b.type == "text"]
        if on_text is not None:
            for block in text_blocks:
                if block.text.strip():
                    on_text(block.text)

        if response.stop_reason == "end_turn":
            final_text = "".join(b.text for b in text_blocks)
            log.info(f"  Loop completed in {iteration} iteration(s)")
            return final_text

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool in tool_use_blocks:
            log.info(f"  Tool: {tool.name}")
            is_error = False
            try:
                result = execute_tool(tool.name, tool.input)
            except Exception as e:  # noqa: BLE001 — tool handlers are user code
                log.error(f"  Tool error ({tool.name}): {e}")
                result = f"Error: {e}"
                is_error = True

            if len(result) > TOOL_RESULT_TRUNCATE_AT:
                result = result[:TOOL_RESULT_TRUNCATE_AT] + "... (truncated)"

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool.id,
                    "content": result,
                    "is_error": is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    log.warning(f"  Hit max iterations ({max_iterations})")
    return "Agent stopped: maximum iterations reached."
