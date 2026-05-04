"""GitHub tools for the commercial agent — repository management, issues, PRs."""

import os
import json
import logging

from .http_utils import robust_request, validate_api_key, AuthError

log = logging.getLogger("commercial-agent")

BASE_URL = "https://api.github.com"


def _headers() -> dict:
    key = validate_api_key("GITHUB_TOKEN")
    return {
        "Authorization": f"Bearer {key}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# --- Tool Definitions ---

GITHUB_TOOLS = [
    {
        "name": "github_search_repos",
        "description": "Search GitHub repositories by query. Use to find relevant repos, check competitors, or explore open-source projects.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g. 'language:python topic:crm')."},
                "per_page": {"type": "integer", "description": "Max results (default 10, max 30)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "github_get_repo",
        "description": "Get details of a specific GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner (user or org)."},
                "repo": {"type": "string", "description": "Repository name."},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "github_list_issues",
        "description": "List issues for a repository. Use to track bugs, feature requests, and tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "description": "Issue state (default: open)."},
                "labels": {"type": "string", "description": "Comma-separated label names to filter by."},
                "per_page": {"type": "integer", "description": "Max results (default 10)."},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "github_create_issue",
        "description": "Create a new issue in a repository. Use for task tracking, bug reports, or feature requests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "title": {"type": "string", "description": "Issue title."},
                "body": {"type": "string", "description": "Issue body (markdown supported)."},
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labels to apply.",
                },
                "assignees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "GitHub usernames to assign.",
                },
            },
            "required": ["owner", "repo", "title"],
        },
    },
    {
        "name": "github_get_issue",
        "description": "Get details of a specific issue including comments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "issue_number": {"type": "integer", "description": "Issue number."},
            },
            "required": ["owner", "repo", "issue_number"],
        },
    },
    {
        "name": "github_add_issue_comment",
        "description": "Add a comment to an existing issue or pull request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "issue_number": {"type": "integer", "description": "Issue or PR number."},
                "body": {"type": "string", "description": "Comment text (markdown supported)."},
            },
            "required": ["owner", "repo", "issue_number", "body"],
        },
    },
    {
        "name": "github_list_pull_requests",
        "description": "List pull requests for a repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "description": "PR state (default: open)."},
                "per_page": {"type": "integer", "description": "Max results (default 10)."},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "github_get_file_contents",
        "description": "Get the contents of a file from a GitHub repository. Use to read READMEs, configs, or any source file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "path": {"type": "string", "description": "File path in the repository."},
                "ref": {"type": "string", "description": "Branch, tag, or commit SHA (default: main)."},
            },
            "required": ["owner", "repo", "path"],
        },
    },
    {
        "name": "github_list_branches",
        "description": "List branches of a repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "per_page": {"type": "integer", "description": "Max results (default 30)."},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "github_list_commits",
        "description": "List recent commits for a repository or specific file path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner."},
                "repo": {"type": "string", "description": "Repository name."},
                "path": {"type": "string", "description": "File path to get commits for (optional)."},
                "per_page": {"type": "integer", "description": "Max results (default 10)."},
            },
            "required": ["owner", "repo"],
        },
    },
]


# --- Tool Execution ---

def execute_github_tool(name: str, input_data: dict) -> str:
    """Execute a GitHub tool and return the result as a string."""
    try:
        if name == "github_search_repos":
            return _search_repos(input_data)
        elif name == "github_get_repo":
            return _get_repo(input_data)
        elif name == "github_list_issues":
            return _list_issues(input_data)
        elif name == "github_create_issue":
            return _create_issue(input_data)
        elif name == "github_get_issue":
            return _get_issue(input_data)
        elif name == "github_add_issue_comment":
            return _add_issue_comment(input_data)
        elif name == "github_list_pull_requests":
            return _list_pull_requests(input_data)
        elif name == "github_get_file_contents":
            return _get_file_contents(input_data)
        elif name == "github_list_branches":
            return _list_branches(input_data)
        elif name == "github_list_commits":
            return _list_commits(input_data)
        else:
            return f"Error: Unknown GitHub tool '{name}'"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


def _search_repos(input_data: dict) -> str:
    params = {"q": input_data["query"], "per_page": input_data.get("per_page", 10)}
    resp = robust_request("GET", f"{BASE_URL}/search/repositories", headers=_headers(), params=params)
    
    data = resp.json()

    results = []
    for repo in data.get("items", []):
        results.append({
            "full_name": repo["full_name"],
            "description": repo.get("description", ""),
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language", ""),
            "url": repo.get("html_url", ""),
            "updated": repo.get("updated_at", ""),
        })

    return json.dumps({"total": data.get("total_count", 0), "repos": results}, ensure_ascii=False)


def _get_repo(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    resp = robust_request("GET", f"{BASE_URL}/repos/{owner}/{repo}", headers=_headers())
    
    r = resp.json()

    return json.dumps({
        "full_name": r["full_name"],
        "description": r.get("description", ""),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "open_issues": r.get("open_issues_count", 0),
        "language": r.get("language", ""),
        "default_branch": r.get("default_branch", "main"),
        "url": r.get("html_url", ""),
        "created": r.get("created_at", ""),
        "updated": r.get("updated_at", ""),
    }, ensure_ascii=False)


def _list_issues(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    params = {
        "state": input_data.get("state", "open"),
        "per_page": input_data.get("per_page", 10),
    }
    if "labels" in input_data:
        params["labels"] = input_data["labels"]

    resp = robust_request("GET", f"{BASE_URL}/repos/{owner}/{repo}/issues", headers=_headers(), params=params)
    

    issues = []
    for issue in resp.json():
        if "pull_request" in issue:
            continue  # Skip PRs (GitHub API returns them mixed with issues)
        issues.append({
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "labels": [l["name"] for l in issue.get("labels", [])],
            "assignees": [a["login"] for a in issue.get("assignees", [])],
            "created": issue.get("created_at", ""),
            "url": issue.get("html_url", ""),
        })

    return json.dumps({"total": len(issues), "issues": issues}, ensure_ascii=False)


def _create_issue(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    payload = {"title": input_data["title"]}
    if "body" in input_data:
        payload["body"] = input_data["body"]
    if "labels" in input_data:
        payload["labels"] = input_data["labels"]
    if "assignees" in input_data:
        payload["assignees"] = input_data["assignees"]

    resp = robust_request("POST", f"{BASE_URL}/repos/{owner}/{repo}/issues", headers=_headers(), json_data=payload)
    
    issue = resp.json()

    return json.dumps({
        "status": "created",
        "number": issue["number"],
        "url": issue.get("html_url", ""),
    }, ensure_ascii=False)


def _get_issue(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    number = input_data["issue_number"]

    resp = robust_request("GET", f"{BASE_URL}/repos/{owner}/{repo}/issues/{number}", headers=_headers())
    
    issue = resp.json()

    # Get comments
    comments_resp = robust_request("GET",
        f"{BASE_URL}/repos/{owner}/{repo}/issues/{number}/comments",
        headers=_headers(),
        params={"per_page": 20},
    )
    comments_
    comments = [
        {"author": c["user"]["login"], "body": c["body"][:500], "created": c["created_at"]}
        for c in comments_resp.json()
    ]

    return json.dumps({
        "number": issue["number"],
        "title": issue["title"],
        "state": issue["state"],
        "body": (issue.get("body") or "")[:2000],
        "labels": [l["name"] for l in issue.get("labels", [])],
        "assignees": [a["login"] for a in issue.get("assignees", [])],
        "comments": comments,
        "url": issue.get("html_url", ""),
    }, ensure_ascii=False)


def _add_issue_comment(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    number = input_data["issue_number"]

    resp = robust_request("POST",
        f"{BASE_URL}/repos/{owner}/{repo}/issues/{number}/comments",
        headers=_headers(),
        json_data={"body": input_data["body"]},
    )
    
    return json.dumps({"status": "comment_added", "id": resp.json()["id"]}, ensure_ascii=False)


def _list_pull_requests(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    params = {
        "state": input_data.get("state", "open"),
        "per_page": input_data.get("per_page", 10),
    }

    resp = robust_request("GET", f"{BASE_URL}/repos/{owner}/{repo}/pulls", headers=_headers(), params=params)
    

    prs = []
    for pr in resp.json():
        prs.append({
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "author": pr["user"]["login"],
            "base": pr["base"]["ref"],
            "head": pr["head"]["ref"],
            "created": pr.get("created_at", ""),
            "url": pr.get("html_url", ""),
        })

    return json.dumps({"total": len(prs), "pull_requests": prs}, ensure_ascii=False)


def _get_file_contents(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    path = input_data["path"]
    params = {}
    if "ref" in input_data:
        params["ref"] = input_data["ref"]

    resp = robust_request("GET",
        f"{BASE_URL}/repos/{owner}/{repo}/contents/{path}",
        headers=_headers(),
        params=params,
    )
    
    data = resp.json()

    if isinstance(data, list):
        # It's a directory
        entries = [{"name": e["name"], "type": e["type"], "path": e["path"]} for e in data]
        return json.dumps({"type": "directory", "entries": entries}, ensure_ascii=False)

    import base64
    content = ""
    if data.get("encoding") == "base64" and data.get("content"):
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")

    return json.dumps({
        "name": data.get("name", ""),
        "path": data.get("path", ""),
        "size": data.get("size", 0),
        "content": content[:5000],
    }, ensure_ascii=False)


def _list_branches(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    params = {"per_page": input_data.get("per_page", 30)}

    resp = robust_request("GET", f"{BASE_URL}/repos/{owner}/{repo}/branches", headers=_headers(), params=params)
    

    branches = [{"name": b["name"], "sha": b["commit"]["sha"][:8]} for b in resp.json()]
    return json.dumps({"total": len(branches), "branches": branches}, ensure_ascii=False)


def _list_commits(input_data: dict) -> str:
    owner, repo = input_data["owner"], input_data["repo"]
    params = {"per_page": input_data.get("per_page", 10)}
    if "path" in input_data:
        params["path"] = input_data["path"]

    resp = robust_request("GET", f"{BASE_URL}/repos/{owner}/{repo}/commits", headers=_headers(), params=params)
    

    commits = []
    for c in resp.json():
        commits.append({
            "sha": c["sha"][:8],
            "message": c["commit"]["message"][:200],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
        })

    return json.dumps({"total": len(commits), "commits": commits}, ensure_ascii=False)
