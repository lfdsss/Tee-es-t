"""Gmail tools for the commercial agent."""

import os
import json
import base64
from email.mime.text import MIMEText
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

_service = None


def _get_gmail_service():
    """Authenticate and return the Gmail API service."""
    global _service
    if _service is not None:
        return _service

    if not GMAIL_AVAILABLE:
        raise RuntimeError("Gmail dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")

    creds = None
    token_path = Path("./config/gmail_token.json")

    # 1. Try loading token from env var (for Railway/serverless)
    token_json = os.getenv("GMAIL_TOKEN_JSON")
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    # 2. Try loading token from file
    if not creds and token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # 3. Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # 4. If no valid token, try OAuth flow (only works locally with browser)
    if not creds or not creds.valid:
        credentials_json = os.getenv("GMAIL_CREDENTIALS_JSON")
        credentials_path = Path(os.getenv("GMAIL_CREDENTIALS_PATH", "./config/gmail_credentials.json"))

        if credentials_json and not credentials_path.exists():
            credentials_path = Path("./config/gmail_credentials.json")
            credentials_path.parent.mkdir(parents=True, exist_ok=True)
            credentials_path.write_text(credentials_json)

        if not credentials_path.exists():
            raise RuntimeError(
                "Gmail not configured. Run 'python setup_gmail.py' on your Mac first, "
                "then add GMAIL_TOKEN_JSON to Railway env vars."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

    # Save token locally
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())

    _service = build("gmail", "v1", credentials=creds)
    return _service


# --- Tool Definitions ---

GMAIL_TOOLS = [
    {
        "name": "gmail_search_messages",
        "description": "Search Gmail messages. Supports Gmail search syntax: from:, to:, subject:, is:unread, has:attachment, after:YYYY/MM/DD, before:YYYY/MM/DD.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g. 'from:client@example.com is:unread').",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum messages to return (default 10).",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "gmail_read_message",
        "description": "Read the full content of a specific Gmail message by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "The Gmail message ID (from gmail_search_messages).",
                },
            },
            "required": ["message_id"],
        },
    },
    {
        "name": "gmail_read_thread",
        "description": "Read an entire email conversation thread.",
        "input_schema": {
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "The Gmail thread ID.",
                },
            },
            "required": ["thread_id"],
        },
    },
    {
        "name": "gmail_create_draft",
        "description": "Create an email draft in Gmail. The draft will NOT be sent automatically — it stays in Drafts for review. Always use this instead of sending directly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject line."},
                "body": {"type": "string", "description": "Email body (plain text)."},
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID to reply to (optional, for replies).",
                },
            },
            "required": ["to", "subject", "body"],
        },
    },
]


# --- Tool Execution ---

def execute_gmail_tool(name: str, input_data: dict) -> str:
    """Execute a Gmail tool and return the result as a string."""
    try:
        if name == "gmail_search_messages":
            return _search_messages(input_data)
        elif name == "gmail_read_message":
            return _read_message(input_data)
        elif name == "gmail_read_thread":
            return _read_thread(input_data)
        elif name == "gmail_create_draft":
            return _create_draft(input_data)
        else:
            return f"Error: Unknown Gmail tool '{name}'"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


def _search_messages(input_data: dict) -> str:
    service = _get_gmail_service()
    query = input_data["query"]
    max_results = input_data.get("max_results", 10)

    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = []
    for msg_ref in result.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        messages.append({
            "id": msg["id"],
            "thread_id": msg["threadId"],
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })

    return json.dumps({"total": result.get("resultSizeEstimate", 0), "messages": messages}, ensure_ascii=False)


def _read_message(input_data: dict) -> str:
    service = _get_gmail_service()
    msg = service.users().messages().get(
        userId="me", id=input_data["message_id"], format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    body = _extract_body(msg.get("payload", {}))

    return json.dumps({
        "id": msg["id"],
        "thread_id": msg["threadId"],
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "body": body,
    }, ensure_ascii=False)


def _read_thread(input_data: dict) -> str:
    service = _get_gmail_service()
    thread = service.users().threads().get(
        userId="me", id=input_data["thread_id"], format="full"
    ).execute()

    messages = []
    for msg in thread.get("messages", []):
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = _extract_body(msg.get("payload", {}))
        messages.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": body[:2000],  # Limit body length per message
        })

    return json.dumps({"thread_id": input_data["thread_id"], "messages": messages}, ensure_ascii=False)


def _create_draft(input_data: dict) -> str:
    service = _get_gmail_service()
    sender = os.getenv("AGENT_OWNER_EMAIL", "me")

    message = MIMEText(input_data["body"])
    message["to"] = input_data["to"]
    message["from"] = sender
    message["subject"] = input_data["subject"]

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"message": {"raw": raw}}

    if "thread_id" in input_data:
        body["message"]["threadId"] = input_data["thread_id"]

    draft = service.users().drafts().create(userId="me", body=body).execute()

    return json.dumps({
        "status": "draft_created",
        "draft_id": draft["id"],
        "message": f"Draft created for {input_data['to']}. Subject: {input_data['subject']}. Review in Gmail before sending.",
    }, ensure_ascii=False)


def _extract_body(payload: dict) -> str:
    """Extract plain text body from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain" and "body" in payload:
        data = payload["body"].get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return ""
