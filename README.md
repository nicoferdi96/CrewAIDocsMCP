# MCP Servers over Streamable HTTP — Complete Guide

📝 **Read the full article here**: [MCP Servers over Streamable HTTP (Step-by-Step)](https://aibootcamp.dev/blog/remote-mcp-servers)

---

This repository provides a complete, production-ready example of building and deploying **MCP (Model Context Protocol) servers** using Python, `mcp`, FastAPI, and uvicorn. You'll learn how to:

- Build MCP servers with custom tools and functions
- Expose tools over HTTP using streamable transport
- Test MCP servers locally with the MCP Inspector
- Deploy MCP servers to production (e.g., Render)
- Connect MCP servers to AI assistants like [Cursor](https://cursor.com/)
- Mount multiple MCP servers in a single FastAPI application

---

## 📁 Project Structure

```bash
.
├── docs/                       # Documentation assets and diagrams
│   └── mcp-client-server.png   # MCP architecture diagram
├── fast_api/                   # Multi-server FastAPI setup
│   ├── crewai_docs_server.py   # CrewAI documentation MCP server
│   ├── echo_server.py          # Simple echo tool MCP server
│   ├── math_server.py          # Math operations MCP server
│   ├── server.py               # FastAPI app mounting all servers
│   └── tavily_server.py        # Tavily web search MCP server
├── services/                   # Shared services and clients
│   ├── __init__.py
│   ├── github_client.py        # GitHub API client for docs
│   └── search_engine.py        # Documentation search engine
├── utils/                      # Utility functions
│   ├── __init__.py
│   └── doc_parser.py           # MDX parsing utilities
├── .gitignore
├── .python-version             # Python 3.11.0
├── CLAUDE.md                   # Codebase documentation for AI assistants
├── pyproject.toml              # Project dependencies and metadata
├── README.md                   # This file
├── runtime.txt                 # Python runtime specification for deployment
├── server.py                   # Standalone Tavily search server
└── uv.lock                     # Dependency lockfile for uv
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (3.12+ recommended)
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Tavily API key for web search functionality (get one at [tavily.com](https://tavily.com))
- OpenAI API key for semantic search (get one at [platform.openai.com](https://platform.openai.com))

### Installation

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone the repository and install dependencies**:
```bash
git clone https://github.com/yourusername/CrewAIDocsMCP.git
cd CrewAIDocsMCP
uv sync
```

3. **Set up environment variables**:
```bash
echo "TAVILY_API_KEY=your_tavily_api_key_here" > .env
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

---

## 🏗️ Building MCP Servers

### Basic MCP Server

The simplest way to create an MCP server is using the `FastMCP` class:

```python
from mcp.server.fastmcp import FastMCP

# Create server instance
mcp = FastMCP("my-server", host="0.0.0.0", port=10000)

# Define tools using decorators
@mcp.tool()
async def my_tool(query: str) -> str:
    """Tool description shown to the AI"""
    return f"Processed: {query}"

# Run the server
mcp.run(transport="streamable-http")
```

### Running the Servers

**Single MCP server (Tavily search):**
```bash
uv run server.py
```

**CrewAI Documentation server:**
```bash
PYTHONPATH=. uv run python fast_api/crewai_docs_server.py
```

**Multiple MCP servers via FastAPI:**
```bash
PYTHONPATH=. uv run python fast_api/server.py
```

This mounts:
- Echo server at `http://localhost:8000/echo/mcp/`
- Math server at `http://localhost:8000/math/mcp/`
- Tavily search at `http://localhost:8000/tavily/mcp/`
- CrewAI docs at `http://localhost:8000/crewai/mcp/`

---

## 🧪 Testing MCP Servers

### Using MCP Inspector

The MCP Inspector is the recommended tool for testing MCP servers during development.

1. **Install the MCP Inspector globally**:
```bash
npm install -g @modelcontextprotocol/inspector
```

2. **Launch the inspector for single server**:
```bash
npx @modelcontextprotocol/inspector http://localhost:10000/mcp/
```

**⚠️ Important**: For streamable HTTP transport, you MUST append `/mcp/` to your server URL.

3. **Testing multiple servers mounted on FastAPI**:

When testing servers mounted on different paths, modify the URL accordingly:

```bash
# Test the echo server
npx @modelcontextprotocol/inspector http://localhost:8000/echo/mcp/

# Test the math server
npx @modelcontextprotocol/inspector http://localhost:8000/math/mcp/

# Test the CrewAI documentation server
npx @modelcontextprotocol/inspector http://localhost:8000/crewai/mcp/

# Test the Tavily search server
npx @modelcontextprotocol/inspector http://localhost:8000/tavily/mcp/
```

### Alternative: Using uv's built-in MCP dev tools

```bash
# Add MCP CLI support to the project
uv add 'mcp[cli]'

# Run the inspector via uv
uv run mcp dev server.py
```

Then navigate to the URL shown (e.g., `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=...`)

---

## 🚀 Deployment

### Deploying to Render

This project is configured for easy deployment to [Render](https://render.com).

1. **Create a new Web Service on Render**

2. **Connect your GitHub repository**

3. **Configure the service**:
   - **Build Command**: `uv sync`
   - **Start Command**: `PYTHONPATH=. uv run python fast_api/server.py`
   - **Environment**: Python 3
   - **Instance Type**: Free or paid tier based on your needs

4. **Add environment variables**:
   - `TAVILY_API_KEY`: Your Tavily API key
   - `OPENAI_API_KEY`: Your OpenAI API key for embeddings
   - `PORT`: Set by Render automatically
   - Any other required secrets

5. **Deploy**: Render will automatically deploy your service

### Environment Variables for Production

The FastAPI server automatically uses the `PORT` environment variable:
```python
port = int(os.getenv("PORT", 8000))
```

### Other Deployment Options

#### Docker
```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Run the server
CMD ["sh", "-c", "PYTHONPATH=. uv run python fast_api/server.py"]
```

#### Heroku
Create a `Procfile`:
```
web: PYTHONPATH=. uv run python fast_api/server.py
```

#### Railway/Fly.io
Use similar configuration with `uv sync` for build and `PYTHONPATH=. uv run python fast_api/server.py` for start command.

---

## 🔌 Connecting to AI Assistants

### Cursor Configuration

1. Open Cursor Settings → MCP Servers
2. Add your server configuration:

**For local development:**
```json
{
  "mcpServers": {
    "tavily-search": {
      "url": "http://localhost:10000/mcp/"
    }
  }
}
```

**For deployed servers:**
```json
{
  "mcpServers": {
    "tavily-search": {
      "url": "https://your-app.onrender.com/mcp/"
    }
  }
}
```

**Multiple servers configuration:**
```json
{
  "mcpServers": {
    "echo-server": {
      "url": "http://localhost:8000/echo/mcp/"
    },
    "math-server": {
      "url": "http://localhost:8000/math/mcp/"
    }
  }
}
```

**⚠️ Important**: Always include the trailing `/` in the URL.

---

## 📚 Available MCP Servers

### 1. Tavily Web Search Server
- **Tool**: `web_search` - Search the web using Tavily API
- **Port**: 10000 (standalone)
- **Requires**: `TAVILY_API_KEY` environment variable

### 2. CrewAI Documentation Server (AI-Powered Vector Search)
- **Tools**:
  - `search_crewai_docs` - AI-powered semantic search using OpenAI embeddings
  - `get_search_suggestions` - Example queries for semantic search
  - `get_search_status` - Check indexing status and progress
  - `list_available_concepts` - Dynamically discovered concept list
  - `get_concept_docs` - Get documentation for specific concepts (auto-discovered)
  - `get_code_examples` - Extract code examples with semantic relevance
  - `get_doc_file` - Retrieve full documentation files
  - `refresh_search_index` - Force refresh of search index
- **Port**: 10001 (standalone)
- **Features**:
  - **AI-powered search**: Semantic search using OpenAI's text-embedding-3-small model
  - **Natural language queries**: Ask questions like "How do I create an agent?"
  - **No timeouts**: Background embedding generation with status tracking
  - **Auto-discovery**: Dynamic concept mapping using pathlib
  - **Persistent embeddings**: Fast server restarts with cached vectors
  - **Smart chunking**: Documents split into ~500 token chunks for granular search
  - **Once-per-day indexing**: Automatic refresh every 24 hours
  - **Category filtering**: Search within specific documentation categories

### 3. Echo Server (Example)
- **Tools**:
  - `echo` - Echo back messages
  - `reverse_echo` - Echo messages in reverse
- **Port**: 9001 (standalone)

### 4. Math Server (Example)
- **Tools**:
  - `add` - Add two numbers
  - `multiply` - Multiply two numbers
  - `calculate` - Evaluate mathematical expressions
- **Port**: 9002 (standalone)

---

## 🛠️ Development

### Local Development Setup

```bash
# Clone and setup
git clone <repository>
cd CrewAIDocsMCP

# Install dependencies
uv sync

# Run single server
uv run server.py

# Or run multi-server FastAPI app
PYTHONPATH=. uv run python fast_api/server.py
```

### Creating New Tools

1. **Create a new MCP server file**:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-tools")

@mcp.tool()
async def my_custom_tool(param: str) -> dict:
    """Description of what this tool does"""
    # Tool implementation
    return {"result": "processed"}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

2. **Test with MCP Inspector**:
```bash
npx @modelcontextprotocol/inspector http://localhost:10000/mcp/
```

3. **Add to FastAPI app** (optional):
```python
# In fast_api/server.py
from my_tools_server import mcp as my_tools_mcp

# Mount the server
app.mount("/my-tools", my_tools_mcp.get_app(with_lifespan=False))
```

### Managing Dependencies

```bash
# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev pytest

# Update all dependencies
uv sync --upgrade

# Lock dependencies
uv lock
```

### Environment Variables

Create a `.env` file in the project root:
```env
TAVILY_API_KEY=your_tavily_api_key
OPENAI_API_KEY=your_openai_api_key
PORT=10000
HOST=0.0.0.0
```

---

## 📚 Resources

- [MCP Documentation](https://github.com/anthropics/model-context-protocol)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Render Deployment Guide](https://render.com/docs)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.