# TaskPilot - MCP Server for ChatGPT Apps

A minimal but fully functional MCP (Model Context Protocol) server built with Python and FastMCP, demonstrating task management with an interactive UI component for ChatGPT.

## Features

- **Two Core Tools**:
  - `add_task(text: str)` - Add a new task to the list
  - `list_tasks()` - Retrieve all tasks with statistics

- **Additional Tools**:
  - `complete_task(task_id: int)` - Mark a task as completed
  - `delete_task(task_id: int)` - Delete a task from the list

- **Interactive UI Widget**:
  - Beautiful, responsive task list interface
  - Add tasks directly from the widget
  - Click to complete/uncomplete tasks
  - Delete tasks with confirmation
  - Real-time statistics (total, pending, completed)
  - Dark mode support

- **In-Memory Storage**: Tasks are stored in memory (resets on server restart)

## Requirements

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### 1. Clone or Download

Navigate to the project directory:

```bash
cd TaskPilot
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Server Locally

Start the server with:

```bash
python server.py
```

You should see output like:

```
============================================================
TaskPilot MCP Server Starting...
============================================================

Server will be available at: http://localhost:8000

To expose this server to ChatGPT:
  1. Install ngrok: https://ngrok.com/download
  2. Run: ngrok http 8000
  3. Copy the HTTPS URL from ngrok
  4. In ChatGPT, go to Developer Mode > Create Connector
  5. Enter the ngrok URL

============================================================

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The server is now running on `http://localhost:8000`.

## Exposing to ChatGPT

Since ChatGPT requires HTTPS access to your server, you need to create a secure tunnel. You have two main options:

### Option 1: Using ngrok (Recommended)

1. **Install ngrok**:
   - Download from: https://ngrok.com/download
   - Or via package manager:
     ```bash
     # macOS
     brew install ngrok

     # Linux
     snap install ngrok
     ```

2. **Sign up and configure** (free tier is sufficient):
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

3. **Start the tunnel** (in a new terminal):
   ```bash
   ngrok http 8000
   ```

4. **Copy the HTTPS URL** from the output:
   ```
   Forwarding  https://abcd-1234-5678.ngrok-free.app -> http://localhost:8000
   ```
   Copy the HTTPS URL (e.g., `https://abcd-1234-5678.ngrok-free.app`)

### Option 2: Using Cloudflare Tunnel

1. **Install cloudflared**:
   - Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

2. **Start the tunnel** (in a new terminal):
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

3. **Copy the HTTPS URL** from the output

## Connecting to ChatGPT

1. **Open ChatGPT** and ensure you have access to ChatGPT Apps (requires ChatGPT Plus or Team)

2. **Enable Developer Mode**:
   - Go to Settings → ChatGPT Apps
   - Enable "Developer Mode"

3. **Create a New Connector**:
   - Click "Create Connector" or "+" button
   - Select "MCP Server" as the connector type

4. **Configure the Connector**:
   - **Name**: TaskPilot
   - **URL**: Paste your ngrok/cloudflared HTTPS URL
   - **MCP Endpoint**: `/mcp` (or leave default if auto-detected)

5. **Save and Test**:
   - Click "Save" or "Create"
   - ChatGPT will verify the connection
   - You should see your tools listed: `add_task`, `list_tasks`, `complete_task`, `delete_task`

## Using TaskPilot in ChatGPT

Once connected, you can interact with TaskPilot directly in ChatGPT:

### Example Prompts:

```
"Show me my tasks"
→ ChatGPT calls list_tasks() and displays the interactive widget

"Add a task to buy groceries"
→ ChatGPT calls add_task(text="buy groceries") and shows updated list

"Mark task 1 as completed"
→ ChatGPT calls complete_task(task_id=1)

"Delete task 2"
→ ChatGPT calls delete_task(task_id=2)
```

### Interactive Widget:

When you ask to view tasks, ChatGPT will display an interactive widget where you can:
- See all tasks with statistics
- Add new tasks using the input field
- Click tasks to toggle completion
- Delete tasks with the trash icon
- View task metadata (ID, creation date)

## Project Structure

```
TaskPilot/
├── server.py           # Main FastMCP server with tool definitions
├── task_list.html      # Interactive UI widget component
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## How It Works

### MCP Server Architecture

1. **FastMCP Server**: Uses the FastMCP library to create an MCP-compliant HTTP server
2. **Tool Registration**: Tools are registered with `@mcp.tool()` decorator
3. **UI Resource**: HTML widget is registered with `@mcp.resource()` decorator
4. **ToolResult**: Each tool returns structured data using `ToolResult` class

### Tool Response Format

Each tool returns:
- **content**: Human-readable text for ChatGPT conversation
- **structured_content**: Machine-readable JSON data for the widget
- **meta**: Metadata including OpenAI-specific fields for UI rendering

Example response from `list_tasks()`:

```python
ToolResult(
    content=[TextContent(
        type="text",
        text="Found 3 task(s): 2 pending, 1 completed"
    )],
    structured_content={
        "tasks": [
            {"id": 1, "text": "Buy groceries", "status": "pending", ...},
            {"id": 2, "text": "Write report", "status": "completed", ...}
        ],
        "total": 2,
        "pending": 1,
        "completed": 1
    },
    meta={
        "operation": "list_tasks",
        "timestamp": "2025-01-15T10:30:00"
    }
)
```

### UI Widget Integration

The HTML widget:
1. Receives `structured_content` via `window.openai.toolOutput`
2. Renders the task list with interactive elements
3. Calls tools via `window.openai.callTool(name, args)`
4. ChatGPT automatically refreshes the widget after tool calls

### Metadata for Widget Rendering

Tools include OpenAI-specific metadata:

```python
meta={
    "openai/outputTemplate": "ui://taskwidget/task_list.html",
    "openai/widgetAccessible": True,
    "openai/resultCanProduceWidget": True,
    "openai/toolInvocation/invoking": "Loading tasks...",
    "openai/toolInvocation/invoked": "Tasks loaded"
}
```

This tells ChatGPT to:
- Render the specified HTML template
- Make the widget interactive
- Show loading/completion messages

## Development

### Running in Development Mode

The server runs with auto-reload enabled by default:

```bash
python server.py
```

Any changes to `server.py` will automatically restart the server.

### Modifying the UI

Edit `task_list.html` to customize the widget appearance or behavior. The server reads this file dynamically, so you'll need to restart the server for changes to take effect.

### Adding New Tools

Add new tools by decorating functions with `@mcp.tool()`:

```python
@mcp.tool(
    meta={
        "openai/outputTemplate": "ui://taskwidget/task_list.html",
        "openai/widgetAccessible": True
    }
)
def my_new_tool(param: str) -> ToolResult:
    """Tool description for the model."""
    return ToolResult(
        content=[TextContent(type="text", text="Result text")],
        structured_content={"data": "value"},
        meta={"custom": "metadata"}
    )
```

## Troubleshooting

### Server Won't Start

- Ensure port 8000 is not in use: `lsof -i :8000` (macOS/Linux)
- Check Python version: `python --version` (requires 3.8+)
- Verify dependencies: `pip install -r requirements.txt`

### ChatGPT Can't Connect

- Verify your tunnel is running (ngrok/cloudflared)
- Ensure you're using the HTTPS URL (not HTTP)
- Check CORS settings in `server.py` (should allow `chatgpt.com`)
- Verify the MCP endpoint is accessible: `https://your-url.ngrok.app/mcp`

### Widget Not Displaying

- Check browser console for JavaScript errors
- Verify `task_list.html` exists in the same directory as `server.py`
- Ensure MIME type is `text/html+skybridge`
- Verify the URI pattern: `ui://taskwidget/task_list.html`

### Tools Not Showing Up

- Check tool registration in `server.py`
- Verify tool schemas are valid
- Restart the server after code changes
- Recreate the connector in ChatGPT

## Production Deployment

For production use, consider:

1. **Persistent Storage**: Replace in-memory storage with a database (SQLite, PostgreSQL, etc.)
2. **Authentication**: Add API key validation or OAuth
3. **Error Handling**: Enhance error messages and logging
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Hosting**: Deploy to a cloud platform (Railway, Render, Heroku, AWS, etc.)
6. **Environment Variables**: Use environment variables for configuration

Example production startup:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

## Technical Specifications

- **MCP Protocol Version**: 2025-06-18
- **FastMCP Version**: 2.0+
- **Content Type**: `text/html+skybridge`
- **Tool Response Format**: ToolResult with structuredContent
- **UI Protocol**: `ui://` resource URIs

## License

MIT License - Feel free to use and modify as needed.

## Resources

- **FastMCP Documentation**: https://gofastmcp.com
- **MCP Specification**: https://modelcontextprotocol.io
- **OpenAI Apps SDK**: https://developers.openai.com/apps-sdk
- **ChatGPT Apps Guide**: https://help.openai.com/en/articles/chatgpt-apps

## Support

For issues or questions:
- FastMCP GitHub: https://github.com/jlowin/fastmcp
- MCP GitHub: https://github.com/modelcontextprotocol
- OpenAI Developer Forum: https://community.openai.com

---

**Happy Task Managing! 🚀**
