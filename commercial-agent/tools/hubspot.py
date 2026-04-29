"""HubSpot CRM tools for the commercial agent."""

import os
import json
import logging

from .http_utils import robust_request, validate_api_key, AuthError

log = logging.getLogger("commercial-agent")

BASE_URL = "https://api.hubapi.com"


def _headers() -> dict:
    key = validate_api_key("HUBSPOT_API_KEY")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


# --- Tool Definitions (sent to Claude) ---

HUBSPOT_TOOLS = [
    {
        "name": "hubspot_search_contacts",
        "description": "Search contacts in HubSpot CRM by name, email, or other criteria. Use this to find existing contacts and check for duplicates before creating new ones.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (name, email, company). Leave empty to list recent contacts.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 10, max 100).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "hubspot_get_contact",
        "description": "Get full details of a specific contact by their HubSpot ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "string",
                    "description": "The HubSpot contact ID.",
                },
            },
            "required": ["contact_id"],
        },
    },
    {
        "name": "hubspot_create_contact",
        "description": "Create a new contact in HubSpot CRM. Always check for duplicates first with hubspot_search_contacts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email address (required)."},
                "firstname": {"type": "string", "description": "First name."},
                "lastname": {"type": "string", "description": "Last name."},
                "phone": {"type": "string", "description": "Phone number."},
                "company": {"type": "string", "description": "Company name."},
                "lifecyclestage": {
                    "type": "string",
                    "description": "Lifecycle stage: subscriber, lead, opportunity, customer.",
                    "enum": ["subscriber", "lead", "opportunity", "customer"],
                },
                "hs_lead_status": {
                    "type": "string",
                    "description": "Lead status.",
                    "enum": ["NEW", "OPEN", "IN_PROGRESS", "CONNECTED"],
                },
            },
            "required": ["email"],
        },
    },
    {
        "name": "hubspot_update_contact",
        "description": "Update properties of an existing contact in HubSpot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "The HubSpot contact ID."},
                "properties": {
                    "type": "object",
                    "description": "Key-value pairs of properties to update (e.g. {'hs_lead_status': 'OPEN', 'phone': '+33...'})",
                },
            },
            "required": ["contact_id", "properties"],
        },
    },
    {
        "name": "hubspot_search_deals",
        "description": "Search deals in the HubSpot pipeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query for deals."},
                "limit": {"type": "integer", "description": "Max results (default 10)."},
            },
            "required": [],
        },
    },
    {
        "name": "hubspot_create_deal",
        "description": "Create a new deal in the HubSpot pipeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dealname": {"type": "string", "description": "Name of the deal."},
                "amount": {"type": "string", "description": "Deal amount."},
                "dealstage": {"type": "string", "description": "Pipeline stage."},
                "closedate": {"type": "string", "description": "Expected close date (YYYY-MM-DD)."},
                "associated_contact_id": {
                    "type": "string",
                    "description": "Contact ID to associate with this deal.",
                },
            },
            "required": ["dealname"],
        },
    },
    {
        "name": "hubspot_create_note",
        "description": "Create a note on a contact or deal in HubSpot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "body": {"type": "string", "description": "Note content."},
                "contact_id": {"type": "string", "description": "Contact ID to attach the note to."},
            },
            "required": ["body", "contact_id"],
        },
    },
    {
        "name": "hubspot_create_task",
        "description": "Create a follow-up task in HubSpot (e.g. reminder to call back).",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Task title."},
                "body": {"type": "string", "description": "Task description."},
                "due_date": {"type": "string", "description": "Due date (YYYY-MM-DD)."},
                "contact_id": {"type": "string", "description": "Contact ID to associate."},
            },
            "required": ["subject"],
        },
    },
]


# --- Tool Execution ---

def execute_hubspot_tool(name: str, input_data: dict) -> str:
    """Execute a HubSpot tool and return the result as a string."""
    try:
        if name == "hubspot_search_contacts":
            return _search_contacts(input_data)
        elif name == "hubspot_get_contact":
            return _get_contact(input_data)
        elif name == "hubspot_create_contact":
            return _create_contact(input_data)
        elif name == "hubspot_update_contact":
            return _update_contact(input_data)
        elif name == "hubspot_search_deals":
            return _search_deals(input_data)
        elif name == "hubspot_create_deal":
            return _create_deal(input_data)
        elif name == "hubspot_create_note":
            return _create_note(input_data)
        elif name == "hubspot_create_task":
            return _create_task(input_data)
        else:
            return f"Error: Unknown HubSpot tool '{name}'"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


def _search_contacts(input_data: dict) -> str:
    query = input_data.get("query", "")
    limit = input_data.get("limit", 10)

    payload = {
        "limit": limit,
        "properties": [
            "firstname", "lastname", "email", "phone", "company",
            "lifecyclestage", "hs_lead_status", "hubspot_owner_id",
        ],
    }
    if query:
        payload["query"] = query

    resp = robust_request("POST",
        f"{BASE_URL}/crm/v3/objects/contacts/search",
        headers=_headers(),
        json=payload,
    )
    
    data = resp.json()

    results = []
    for contact in data.get("results", []):
        props = contact.get("properties", {})
        results.append({
            "id": contact["id"],
            "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
            "email": props.get("email", ""),
            "phone": props.get("phone", ""),
            "company": props.get("company", ""),
            "stage": props.get("lifecyclestage", ""),
            "status": props.get("hs_lead_status", ""),
        })

    return json.dumps({"total": data.get("total", 0), "contacts": results}, ensure_ascii=False)


def _get_contact(input_data: dict) -> str:
    contact_id = input_data["contact_id"]
    resp = robust_request("GET",
        f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}",
        headers=_headers(),
        params={
            "properties": "firstname,lastname,email,phone,company,lifecyclestage,hs_lead_status,hubspot_owner_id,createdate,lastmodifieddate",
        },
    )
    
    return json.dumps(resp.json(), ensure_ascii=False)


def _create_contact(input_data: dict) -> str:
    owner_id = os.getenv("HUBSPOT_OWNER_ID", "")
    properties = {
        "email": input_data["email"],
        "hubspot_owner_id": owner_id,
    }
    for field in ["firstname", "lastname", "phone", "company", "lifecyclestage", "hs_lead_status"]:
        if field in input_data:
            properties[field] = input_data[field]

    if "lifecyclestage" not in properties:
        properties["lifecyclestage"] = "lead"
    if "hs_lead_status" not in properties:
        properties["hs_lead_status"] = "NEW"

    resp = robust_request("POST",
        f"{BASE_URL}/crm/v3/objects/contacts",
        headers=_headers(),
        json={"properties": properties},
    )
    
    result = resp.json()
    return json.dumps({
        "status": "created",
        "id": result["id"],
        "properties": result.get("properties", {}),
    }, ensure_ascii=False)


def _update_contact(input_data: dict) -> str:
    contact_id = input_data["contact_id"]
    properties = input_data["properties"]

    resp = robust_request("PATCH",
        f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}",
        headers=_headers(),
        json={"properties": properties},
    )
    
    return json.dumps({"status": "updated", "id": contact_id}, ensure_ascii=False)


def _search_deals(input_data: dict) -> str:
    query = input_data.get("query", "")
    limit = input_data.get("limit", 10)

    payload = {
        "limit": limit,
        "properties": ["dealname", "dealstage", "amount", "closedate", "hubspot_owner_id"],
    }
    if query:
        payload["query"] = query

    resp = robust_request("POST",
        f"{BASE_URL}/crm/v3/objects/deals/search",
        headers=_headers(),
        json=payload,
    )
    
    return json.dumps(resp.json(), ensure_ascii=False)


def _create_deal(input_data: dict) -> str:
    owner_id = os.getenv("HUBSPOT_OWNER_ID", "")
    properties = {
        "dealname": input_data["dealname"],
        "hubspot_owner_id": owner_id,
    }
    for field in ["amount", "dealstage", "closedate"]:
        if field in input_data:
            properties[field] = input_data[field]

    if "dealstage" not in properties:
        properties["dealstage"] = "appointmentscheduled"

    resp = robust_request("POST",
        f"{BASE_URL}/crm/v3/objects/deals",
        headers=_headers(),
        json={"properties": properties},
    )
    
    result = resp.json()

    # Associate with contact if provided
    if "associated_contact_id" in input_data:
        robust_request("PUT",
            f"{BASE_URL}/crm/v3/objects/deals/{result['id']}/associations/contacts/{input_data['associated_contact_id']}/deal_to_contact",
            headers=_headers(),
        )

    return json.dumps({"status": "created", "id": result["id"]}, ensure_ascii=False)


def _create_note(input_data: dict) -> str:
    resp = robust_request("POST",
        f"{BASE_URL}/crm/v3/objects/notes",
        headers=_headers(),
        json={
            "properties": {"hs_note_body": input_data["body"]},
            "associations": [
                {
                    "to": {"id": input_data["contact_id"]},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
                }
            ],
        },
    )
    
    return json.dumps({"status": "created", "id": resp.json()["id"]}, ensure_ascii=False)


def _create_task(input_data: dict) -> str:
    owner_id = os.getenv("HUBSPOT_OWNER_ID", "")
    properties = {
        "hs_task_subject": input_data["subject"],
        "hubspot_owner_id": owner_id,
        "hs_task_status": "NOT_STARTED",
    }
    if "body" in input_data:
        properties["hs_task_body"] = input_data["body"]
    if "due_date" in input_data:
        properties["hs_timestamp"] = input_data["due_date"]

    associations = []
    if "contact_id" in input_data:
        associations.append({
            "to": {"id": input_data["contact_id"]},
            "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 204}],
        })

    resp = robust_request("POST",
        f"{BASE_URL}/crm/v3/objects/tasks",
        headers=_headers(),
        json={"properties": properties, "associations": associations},
    )
    
    return json.dumps({"status": "created", "id": resp.json()["id"]}, ensure_ascii=False)
