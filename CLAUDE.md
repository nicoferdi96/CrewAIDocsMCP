# CrewAIDocsMCP - Codebase Analysis

## Overview

This codebase is a demonstration project for building and running **MCP (Model Context Protocol) servers** using Python. It showcases how to expose tools and functions over HTTP using the MCP protocol, enabling AI assistants like Cursor to connect to custom tools via streamable HTTP transport.

## Project Purpose

The project serves as a step-by-step guide and working example for:
- Building MCP servers with Python using the `mcp` library and FastAPI
- Exposing custom tools and functions that AI assistants can use
- Implementing streamable HTTP as the transport layer
- Mounting multiple MCP servers in a single FastAPI application

## Directory Structure

### Root Level Files
- **`server.py`**: The main standalone MCP server that implements a web search tool using the Tavily API
- **`pyproject.toml`**: Project configuration defining dependencies (FastAPI, mcp, python-dotenv, tavily-python)
- **`readme.md`**: Main documentation with setup instructions and usage guide
- **`runtime.txt`**: Specifies Python 3.11.0 for deployment platforms
- **`uv.lock`**: Lockfile for the `uv` dependency manager

### `/fastapi_example/`
Contains examples of mounting multiple MCP servers in a single FastAPI application:
- **`server.py`**: FastAPI app that mounts both echo and math servers at different endpoints
- **`echo_server.py`**: Simple MCP server with echo and secret_phrase tools
- **`math_server.py`**: Simple MCP server with a basic math addition tool

### `/docs/`
- **`mcp-client-server.png`**: Diagram illustrating the MCP client-server architecture

## Tech Stack

- **Python 3.11+** (3.12+ preferred based on pyproject.toml)
- **FastAPI**: Web framework for creating HTTP endpoints
- **MCP (Model Context Protocol)**: Protocol for AI-tool communication
- **Tavily API**: Web search service used in the main example
- **UV**: Modern Python package manager (recommended)
- **python-dotenv**: Environment variable management

## Main Entry Points

1. **Basic MCP Server**: `/server.py`
   - Runs a single MCP server with web search functionality
   - Default port: 10000
   - Requires `TAVILY_API_KEY` environment variable

2. **Multi-Server FastAPI App**: `/fastapi_example/server.py`
   - Mounts multiple MCP servers at different paths
   - Echo server at `/echo/mcp/`
   - Math server at `/math/mcp/`
   - Demonstrates lifecycle management for multiple servers

## Key Components

### MCP Server Implementation Pattern
```python
from mcp.server.fastmcp import FastMCP

# Create server instance
mcp = FastMCP("server-name", host="0.0.0.0", port=PORT)

# Define tools using decorators
@mcp.tool()
def tool_name(param: str) -> str:
    """Tool description"""
    return result

# Run the server
mcp.run(transport="streamable-http")
```

### FastAPI Integration Pattern
- Uses `AsyncExitStack` for managing multiple server lifecycles
- Mounts MCP servers as sub-applications
- Provides unified endpoint management

## Configuration

### Environment Variables
- **`TAVILY_API_KEY`**: Required for the web search functionality
- **`PORT`**: Server port (defaults to 10000)

### Client Configuration (Cursor)
```json
{
  "mcpServers": {
    "server-name": {
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

## Development Workflow

1. **Setup**: Use `uv` for dependency management
2. **Debug**: MCP Inspector available via `uv run mcp dev server.py`
3. **Deploy**: Compatible with platforms like Render (uses runtime.txt)

## Architecture Notes

- Uses **streamable HTTP** transport for real-time communication
- Supports both stateless and stateful server modes
- Tools are exposed as decorated Python functions
- FastAPI enables mounting multiple MCP servers on different routes

This codebase serves as both a learning resource and a template for building production MCP servers that can extend AI assistant capabilities with custom tools.