"""Notion tools for the commercial agent — project management, documentation, CRM notes."""

import os
import json
import logging

from .http_utils import robust_request, validate_api_key, AuthError

log = logging.getLogger("commercial-agent")

BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    key = validate_api_key("NOTION_API_KEY")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


# --- Tool Definitions ---

NOTION_TOOLS = [
    {
        "name": "notion_search",
        "description": "Search across all Notion pages and databases. Use to find existing documents, projects, notes, or any content in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text."},
                "filter_type": {
                    "type": "string",
                    "description": "Filter by object type.",
                    "enum": ["page", "database"],
                },
                "page_size": {"type": "integer", "description": "Max results (default 10, max 100)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "notion_get_page",
        "description": "Retrieve a Notion page's properties and metadata by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "The Notion page ID (UUID)."},
            },
            "required": ["page_id"],
        },
    },
    {
        "name": "notion_create_page",
        "description": "Create a new page in Notion. Can be a standalone page or a row in a database. Use for creating meeting notes, project briefs, prospect profiles, or any documentation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_type": {
                    "type": "string",
                    "description": "Type of parent: 'database_id' to add a row to a database, 'page_id' to create a subpage.",
                    "enum": ["database_id", "page_id"],
                },
                "parent_id": {"type": "string", "description": "ID of the parent database or page."},
                "title": {"type": "string", "description": "Page title."},
                "properties": {
                    "type": "object",
                    "description": "Database properties as key-value pairs (for database rows). E.g. {'Status': {'select': {'name': 'In Progress'}}, 'Priority': {'select': {'name': 'High'}}}",
                },
                "content": {
                    "type": "string",
                    "description": "Page content in markdown format. Will be converted to Notion blocks.",
                },
            },
            "required": ["parent_type", "parent_id", "title"],
        },
    },
    {
        "name": "notion_update_page",
        "description": "Update properties of an existing Notion page. Use to change status, add tags, update fields in database rows.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "The Notion page ID to update."},
                "properties": {
                    "type": "object",
                    "description": "Properties to update as key-value pairs.",
                },
            },
            "required": ["page_id", "properties"],
        },
    },
    {
        "name": "notion_create_database",
        "description": "Create a new database in Notion. Use for creating tracking tables (prospect pipeline, project tracker, content calendar, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_page_id": {"type": "string", "description": "ID of the parent page where the database will be created."},
                "title": {"type": "string", "description": "Database title."},
                "properties": {
                    "type": "object",
                    "description": "Database schema as a dict of property names to property configs. E.g. {'Name': {'title': {}}, 'Status': {'select': {'options': [{'name': 'New'}, {'name': 'Done'}]}}, 'Email': {'email': {}}}",
                },
            },
            "required": ["parent_page_id", "title", "properties"],
        },
    },
    {
        "name": "notion_query_database",
        "description": "Query a Notion database with optional filters and sorts. Use to retrieve CRM data, project lists, or any structured data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database_id": {"type": "string", "description": "The database ID to query."},
                "filter": {
                    "type": "object",
                    "description": "Notion filter object. E.g. {'property': 'Status', 'select': {'equals': 'Active'}}",
                },
                "sorts": {
                    "type": "array",
                    "description": "Sort criteria. E.g. [{'property': 'Created', 'direction': 'descending'}]",
                    "items": {"type": "object"},
                },
                "page_size": {"type": "integer", "description": "Max results (default 100)."},
            },
            "required": ["database_id"],
        },
    },
    {
        "name": "notion_add_comment",
        "description": "Add a comment to a Notion page. Use for logging activities, leaving notes on prospects, or team communication.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "The page ID to comment on."},
                "text": {"type": "string", "description": "Comment text content."},
            },
            "required": ["page_id", "text"],
        },
    },
]


# --- Tool Execution ---

def execute_notion_tool(name: str, input_data: dict) -> str:
    """Execute a Notion tool and return the result as a string."""
    try:
        if name == "notion_search":
            return _search(input_data)
        elif name == "notion_get_page":
            return _get_page(input_data)
        elif name == "notion_create_page":
            return _create_page(input_data)
        elif name == "notion_update_page":
            return _update_page(input_data)
        elif name == "notion_create_database":
            return _create_database(input_data)
        elif name == "notion_query_database":
            return _query_database(input_data)
        elif name == "notion_add_comment":
            return _add_comment(input_data)
        else:
            return f"Error: Unknown Notion tool '{name}'"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


def _search(input_data: dict) -> str:
    payload = {"query": input_data["query"]}
    if "filter_type" in input_data:
        payload["filter"] = {"value": input_data["filter_type"], "property": "object"}
    if "page_size" in input_data:
        payload["page_size"] = input_data["page_size"]

    resp = robust_request("POST", f"{BASE_URL}/search", headers=_headers(), json_data=payload)
    
    data = resp.json()

    results = []
    for item in data.get("results", []):
        obj = {"id": item["id"], "type": item["object"]}
        if item["object"] == "page":
            title_prop = item.get("properties", {}).get("title", item.get("properties", {}).get("Name", {}))
            if isinstance(title_prop, dict) and "title" in title_prop:
                titles = title_prop["title"]
                obj["title"] = "".join(t.get("plain_text", "") for t in titles) if isinstance(titles, list) else ""
            obj["url"] = item.get("url", "")
        elif item["object"] == "database":
            titles = item.get("title", [])
            obj["title"] = "".join(t.get("plain_text", "") for t in titles)
            obj["url"] = item.get("url", "")
        results.append(obj)

    return json.dumps({"total": len(results), "results": results}, ensure_ascii=False)


def _get_page(input_data: dict) -> str:
    page_id = input_data["page_id"]
    resp = robust_request("GET", f"{BASE_URL}/pages/{page_id}", headers=_headers())
    
    page = resp.json()

    # Simplify properties for readability
    props_summary = {}
    for key, val in page.get("properties", {}).items():
        prop_type = val.get("type", "")
        if prop_type == "title":
            props_summary[key] = "".join(t.get("plain_text", "") for t in val.get("title", []))
        elif prop_type == "rich_text":
            props_summary[key] = "".join(t.get("plain_text", "") for t in val.get("rich_text", []))
        elif prop_type == "select":
            sel = val.get("select")
            props_summary[key] = sel.get("name", "") if sel else None
        elif prop_type == "multi_select":
            props_summary[key] = [s.get("name", "") for s in val.get("multi_select", [])]
        elif prop_type == "email":
            props_summary[key] = val.get("email")
        elif prop_type == "phone_number":
            props_summary[key] = val.get("phone_number")
        elif prop_type == "url":
            props_summary[key] = val.get("url")
        elif prop_type == "number":
            props_summary[key] = val.get("number")
        elif prop_type == "checkbox":
            props_summary[key] = val.get("checkbox")
        elif prop_type == "date":
            date_val = val.get("date")
            props_summary[key] = date_val.get("start") if date_val else None
        else:
            props_summary[key] = f"[{prop_type}]"

    return json.dumps({
        "id": page["id"],
        "url": page.get("url", ""),
        "created": page.get("created_time", ""),
        "updated": page.get("last_edited_time", ""),
        "properties": props_summary,
    }, ensure_ascii=False)


def _create_page(input_data: dict) -> str:
    parent_type = input_data["parent_type"]
    parent_id = input_data["parent_id"]
    title = input_data["title"]

    payload = {"parent": {parent_type: parent_id}}

    if parent_type == "database_id":
        properties = input_data.get("properties", {})
        # Find the title property name (could be "Name", "Title", etc.)
        # Default to "Name" if not specified in properties
        title_key = "Name"
        for key, val in properties.items():
            if isinstance(val, dict) and "title" in val:
                title_key = key
                break
        properties[title_key] = {"title": [{"text": {"content": title}}]}
        payload["properties"] = properties
    else:
        payload["properties"] = {
            "title": {"title": [{"text": {"content": title}}]}
        }

    # Add content as children blocks
    if "content" in input_data:
        payload["children"] = _markdown_to_blocks(input_data["content"])

    resp = robust_request("POST", f"{BASE_URL}/pages", headers=_headers(), json_data=payload)
    
    result = resp.json()
    return json.dumps({
        "status": "created",
        "id": result["id"],
        "url": result.get("url", ""),
    }, ensure_ascii=False)


def _update_page(input_data: dict) -> str:
    page_id = input_data["page_id"]
    properties = input_data["properties"]

    resp = robust_request("PATCH",
        f"{BASE_URL}/pages/{page_id}",
        headers=_headers(),
        json={"properties": properties},
    )
    
    return json.dumps({"status": "updated", "id": page_id}, ensure_ascii=False)


def _create_database(input_data: dict) -> str:
    parent_page_id = input_data["parent_page_id"]
    title = input_data["title"]
    properties = input_data["properties"]

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties,
    }

    resp = robust_request("POST", f"{BASE_URL}/databases", headers=_headers(), json_data=payload)
    
    result = resp.json()
    return json.dumps({
        "status": "created",
        "id": result["id"],
        "url": result.get("url", ""),
    }, ensure_ascii=False)


def _query_database(input_data: dict) -> str:
    database_id = input_data["database_id"]
    payload = {}
    if "filter" in input_data:
        payload["filter"] = input_data["filter"]
    if "sorts" in input_data:
        payload["sorts"] = input_data["sorts"]
    payload["page_size"] = input_data.get("page_size", 100)

    resp = robust_request("POST",
        f"{BASE_URL}/databases/{database_id}/query",
        headers=_headers(),
        json_data=payload,
    )
    
    data = resp.json()

    rows = []
    for page in data.get("results", []):
        row = {"id": page["id"], "url": page.get("url", "")}
        for key, val in page.get("properties", {}).items():
            prop_type = val.get("type", "")
            if prop_type == "title":
                row[key] = "".join(t.get("plain_text", "") for t in val.get("title", []))
            elif prop_type == "rich_text":
                row[key] = "".join(t.get("plain_text", "") for t in val.get("rich_text", []))
            elif prop_type == "select":
                sel = val.get("select")
                row[key] = sel.get("name", "") if sel else None
            elif prop_type == "multi_select":
                row[key] = [s.get("name", "") for s in val.get("multi_select", [])]
            elif prop_type == "number":
                row[key] = val.get("number")
            elif prop_type == "email":
                row[key] = val.get("email")
            elif prop_type == "date":
                d = val.get("date")
                row[key] = d.get("start") if d else None
            elif prop_type == "checkbox":
                row[key] = val.get("checkbox")
            elif prop_type == "status":
                s = val.get("status")
                row[key] = s.get("name", "") if s else None
        rows.append(row)

    return json.dumps({
        "total": len(rows),
        "has_more": data.get("has_more", False),
        "rows": rows,
    }, ensure_ascii=False)


def _add_comment(input_data: dict) -> str:
    page_id = input_data["page_id"]
    text = input_data["text"]

    resp = robust_request("POST",
        f"{BASE_URL}/comments",
        headers=_headers(),
        json_data={
            "parent": {"page_id": page_id},
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    )
    
    return json.dumps({"status": "comment_added", "id": resp.json()["id"]}, ensure_ascii=False)


def _markdown_to_blocks(markdown: str) -> list:
    """Convert simple markdown to Notion blocks."""
    blocks = []
    for line in markdown.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]},
            })
        elif stripped.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": stripped[3:]}}]},
            })
        elif stripped.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": stripped[4:]}}]},
            })
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]},
            })
        elif stripped.startswith("[] ") or stripped.startswith("[ ] "):
            text = stripped.replace("[] ", "", 1).replace("[ ] ", "", 1)
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {"rich_text": [{"type": "text", "text": {"content": text}}], "checked": False},
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": stripped}}]},
            })
    return blocks
