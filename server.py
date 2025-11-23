"""
TaskPilot MCP Server
A minimal MCP server for ChatGPT Apps demonstrating task management with interactive UI.
"""

from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from starlette.middleware.cors import CORSMiddleware

# Initialize FastMCP server
mcp = FastMCP(name="taskpilot")

# JSON file for persistent storage
TASKS_FILE = Path("tasks.json")

# In-memory task storage
tasks: List[Dict[str, Any]] = []
task_id_counter = 1


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


# Load tasks on startup
load_tasks()


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
