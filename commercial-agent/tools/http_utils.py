"""HTTP utilities with timeouts, retries, and structured error handling."""

import time
import logging
import requests

log = logging.getLogger("commercial-agent")

DEFAULT_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_BACKOFF = 2


def robust_request(
    method: str,
    url: str,
    headers: dict = None,
    json_data: dict = None,
    params: dict = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = MAX_RETRIES,
) -> requests.Response:
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=timeout,
            )
            if resp.status_code == 429:
                wait = RETRY_BACKOFF ** attempt
                log.warning(f"Rate limited (429) on {url}, waiting {wait}s (attempt {attempt}/{retries})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout as e:
            last_exc = e
            log.warning(f"Timeout on {url} (attempt {attempt}/{retries})")
            if attempt < retries:
                time.sleep(RETRY_BACKOFF ** attempt)
        except requests.exceptions.ConnectionError as e:
            last_exc = e
            log.warning(f"Connection error on {url} (attempt {attempt}/{retries})")
            if attempt < retries:
                time.sleep(RETRY_BACKOFF ** attempt)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            if status in (401, 403):
                raise AuthError(f"Auth failed ({status}) on {url}: check API key") from e
            if status >= 500 and attempt < retries:
                log.warning(f"Server error ({status}) on {url}, retrying (attempt {attempt}/{retries})")
                time.sleep(RETRY_BACKOFF ** attempt)
                last_exc = e
                continue
            raise
    raise last_exc or requests.exceptions.RequestException(f"Failed after {retries} attempts: {url}")


class AuthError(Exception):
    pass


def validate_api_key(key_name: str) -> str:
    import os
    val = os.getenv(key_name, "").strip()
    if not val:
        raise AuthError(f"Missing environment variable: {key_name}")
    return val
