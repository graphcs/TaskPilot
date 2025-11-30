"""
TaskPilot MCP Server
A minimal MCP server for ChatGPT Apps demonstrating task management with interactive UI.
Includes a Crunchbase-style startup database with company information.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from starlette.middleware.cors import CORSMiddleware

# Initialize FastMCP server
mcp = FastMCP(name="taskpilot")

# JSON files for persistent storage
TASKS_FILE = Path("tasks.json")
COMPANIES_FILE = Path("companies.json")

# In-memory task storage
tasks: List[Dict[str, Any]] = []
task_id_counter = 1

# In-memory company storage
companies_data: Dict[str, Any] = {"companies": [], "industries": [], "funding_stages": []}


def load_companies() -> None:
    """Load companies from JSON file"""
    global companies_data

    if COMPANIES_FILE.exists():
        try:
            with open(COMPANIES_FILE, 'r') as f:
                companies_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading companies: {e}")
            companies_data = {"companies": [], "industries": [], "funding_stages": []}


def load_tasks() -> None:
    """Load tasks from JSON file"""
    global tasks, task_id_counter

    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
                tasks = data.get('tasks', [])
                task_id_counter = data.get('task_id_counter', 1)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading tasks: {e}")
            tasks = []
            task_id_counter = 1
    else:
        tasks = []
        task_id_counter = 1


def save_tasks() -> None:
    """Save tasks to JSON file"""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump({
                'tasks': tasks,
                'task_id_counter': task_id_counter
            }, f, indent=2)
    except IOError as e:
        print(f"Error saving tasks: {e}")


# Load data on startup
load_tasks()
load_companies()


@mcp.tool()
def add_task(text: str) -> ToolResult:
    """
    Add a new task to the task list.

    Args:
        text: The task description text

    Returns:
        Updated task list with the newly added task
    """
    global task_id_counter, tasks

    new_task = {
        "id": task_id_counter,
        "text": text,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

    tasks.append(new_task)
    task_id_counter += 1
    save_tasks()

    return ToolResult(
        content=[TextContent(
            type="text",
            text=f"Added task: '{text}'. Total tasks: {len(tasks)}"
        )],
        structured_content={
            "tasks": tasks,
            "total": len(tasks),
            "latest_task": new_task
        },
        meta={
            "operation": "add_task",
            "task_id": new_task["id"]
        }
    )


@mcp.tool()
def list_tasks() -> ToolResult:
    """
    Retrieve all tasks from the task list.

    Returns:
        Complete list of all tasks with their details
    """
    pending_count = sum(1 for t in tasks if t["status"] == "pending")
    completed_count = sum(1 for t in tasks if t["status"] == "completed")

    if len(tasks) == 0:
        message = "No tasks found. Add your first task to get started!"
    else:
        message = f"Found {len(tasks)} task(s): {pending_count} pending, {completed_count} completed"

    return ToolResult(
        content=[TextContent(
            type="text",
            text=message
        )],
        structured_content={
            "tasks": tasks,
            "total": len(tasks),
            "pending": pending_count,
            "completed": completed_count
        },
        meta={
            "operation": "list_tasks",
            "timestamp": datetime.now().isoformat()
        }
    )


@mcp.tool()
def complete_task(task_id: int) -> ToolResult:
    """
    Mark a task as completed.

    Args:
        task_id: The ID of the task to mark as completed

    Returns:
        Updated task list with the task marked as completed
    """
    global tasks

    task_found = False
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task_found = True
            break

    if not task_found:
        return ToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: Task with ID {task_id} not found"
            )],
            structured_content={
                "error": "Task not found",
                "task_id": task_id
            },
            meta={
                "operation": "complete_task",
                "success": False
            }
        )

    save_tasks()

    return ToolResult(
        content=[TextContent(
            type="text",
            text=f"Task {task_id} marked as completed"
        )],
        structured_content={
            "tasks": tasks,
            "total": len(tasks),
            "task_id": task_id
        },
        meta={
            "operation": "complete_task",
            "success": True,
            "task_id": task_id
        }
    )


@mcp.tool()
def delete_task(task_id: int) -> ToolResult:
    """
    Delete a task from the task list.

    Args:
        task_id: The ID of the task to delete

    Returns:
        Updated task list with the task removed
    """
    global tasks

    initial_count = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]

    if len(tasks) == initial_count:
        return ToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: Task with ID {task_id} not found"
            )],
            structured_content={
                "error": "Task not found",
                "task_id": task_id
            },
            meta={
                "operation": "delete_task",
                "success": False
            }
        )

    save_tasks()

    return ToolResult(
        content=[TextContent(
            type="text",
            text=f"Task {task_id} deleted successfully"
        )],
        structured_content={
            "tasks": tasks,
            "total": len(tasks)
        },
        meta={
            "operation": "delete_task",
            "success": True,
            "task_id": task_id
        }
    )


# =============================================================================
# COMPANY DATABASE TOOLS
# =============================================================================

def format_currency(amount: int) -> str:
    """Format currency in human-readable form (e.g., $45M, $3.2M)"""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M" if amount % 1_000_000 == 0 else f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount}"


def format_funding_history(history: List[str]) -> str:
    """Format funding history as arrow-separated string"""
    return " → ".join(history)


@mcp.tool(
    meta={
        "openai/outputTemplate": "ui://companydb/widget.html",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True
    }
)
def list_companies(
    industry: Optional[str] = None,
    funding_stage: Optional[str] = None,
    hq: Optional[str] = None,
    year: Optional[int] = None,
    search: Optional[str] = None
) -> ToolResult:
    """
    List all startup companies with optional filtering.

    Args:
        industry: Filter by industry (e.g., "Biotechnology", "AI/ML", "Fintech")
        funding_stage: Filter by last funding stage (e.g., "Seed", "Series A", "Series B")
        hq: Filter by headquarters location
        year: Filter by year founded
        search: Search by company name or tagline

    Returns:
        List of companies matching the filters with widget for display
    """
    companies = companies_data.get("companies", [])

    # Apply filters
    if industry:
        companies = [c for c in companies if c.get("industry", "").lower() == industry.lower()]

    if funding_stage:
        companies = [c for c in companies if c.get("last_round", "").lower() == funding_stage.lower()]

    if hq:
        companies = [c for c in companies if hq.lower() in c.get("hq", "").lower()]

    if year:
        companies = [c for c in companies if c.get("year_founded") == year]

    if search:
        search_lower = search.lower()
        companies = [c for c in companies if
                    search_lower in c.get("name", "").lower() or
                    search_lower in c.get("tagline", "").lower() or
                    search_lower in c.get("description", "").lower()]

    # Build summary message
    if len(companies) == 0:
        message = "No companies found matching the criteria."
    else:
        message = f"Found {len(companies)} startup(s)"
        if industry:
            message += f" in {industry}"
        if funding_stage:
            message += f" at {funding_stage} stage"

    return ToolResult(
        content=[TextContent(
            type="text",
            text=message
        )],
        structured_content={
            "companies": companies,
            "total": len(companies),
            "industries": companies_data.get("industries", []),
            "funding_stages": companies_data.get("funding_stages", [])
        },
        meta={
            "operation": "list_companies",
            "openai/outputTemplate": "ui://companydb/widget.html"
        }
    )


@mcp.tool()
def get_company(company_id: int) -> ToolResult:
    """
    Get detailed information for a specific company.

    Args:
        company_id: The unique ID of the company

    Returns:
        Full company details including description and funding info
    """
    companies = companies_data.get("companies", [])
    company = next((c for c in companies if c.get("id") == company_id), None)

    if not company:
        return ToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: Company with ID {company_id} not found"
            )],
            structured_content={
                "error": "Company not found",
                "company_id": company_id
            },
            meta={
                "operation": "get_company",
                "success": False
            }
        )

    # Format for display
    funding_str = format_funding_history(company.get("funding_history", []))
    round_size = format_currency(company.get("last_round_size", 0))
    valuation = format_currency(company.get("valuation", 0))

    message = f"""
{company['name']} - {company.get('tagline', '')}

Location: {company.get('hq', 'Unknown')}
Founded: {company.get('year_founded', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Employees: {company.get('employees', 'Unknown')}

{company.get('description', '')}

Funding History: {funding_str}
Last Round: {company.get('last_round', 'Unknown')} ({round_size})
Valuation: {valuation}
"""

    return ToolResult(
        content=[TextContent(
            type="text",
            text=message.strip()
        )],
        structured_content={
            "company": company,
            "formatted": {
                "funding_history": funding_str,
                "last_round_size": round_size,
                "valuation": valuation
            }
        },
        meta={
            "operation": "get_company",
            "success": True,
            "company_id": company_id
        }
    )


@mcp.tool(
    meta={
        "openai/outputTemplate": "ui://companydb/widget.html",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True
    }
)
def search_companies(query: str) -> ToolResult:
    """
    Search companies by name, tagline, or description.

    Args:
        query: Search query string

    Returns:
        List of companies matching the search query
    """
    companies = companies_data.get("companies", [])
    query_lower = query.lower()

    matching = [c for c in companies if
                query_lower in c.get("name", "").lower() or
                query_lower in c.get("tagline", "").lower() or
                query_lower in c.get("description", "").lower() or
                query_lower in c.get("industry", "").lower()]

    if len(matching) == 0:
        message = f"No companies found matching '{query}'"
    else:
        message = f"Found {len(matching)} company(ies) matching '{query}'"

    return ToolResult(
        content=[TextContent(
            type="text",
            text=message
        )],
        structured_content={
            "companies": matching,
            "total": len(matching),
            "query": query,
            "industries": companies_data.get("industries", []),
            "funding_stages": companies_data.get("funding_stages", [])
        },
        meta={
            "operation": "search_companies",
            "openai/outputTemplate": "ui://companydb/widget.html"
        }
    )


# =============================================================================
# WIDGET RESOURCES
# =============================================================================

@mcp.resource(
    uri="ui://companydb/widget.html",
    mime_type="text/html+skybridge",
    name="Company Database Widget"
)
def company_widget() -> str:
    """Serve the company database widget HTML"""
    widget_path = Path("company_widget.html")
    if widget_path.exists():
        with open(widget_path, "r") as f:
            return f.read()
    return "<html><body>Widget not found</body></html>"


# Create HTTP app with CORS support
app = mcp.http_app(stateless_http=True)

# Configure CORS for ChatGPT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com", "https://chat.openai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("TaskPilot MCP Server Starting...")
    print("=" * 60)
    print("\nServer will be available at: http://localhost:8000")
    print("\nTo expose this server to ChatGPT:")
    print("  1. Install ngrok: https://ngrok.com/download")
    print("  2. Run: ngrok http 8000")
    print("  3. Copy the HTTPS URL from ngrok")
    print("  4. In ChatGPT, go to Developer Mode > Create Connector")
    print("  5. Enter the ngrok URL")
    print("\n" + "=" * 60 + "\n")

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
