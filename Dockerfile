FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy all project files
COPY . .

# Install dependencies directly from pyproject.toml
RUN uv pip install --system --no-cache-dir .

# Create necessary directories
RUN mkdir -p /app/docs_cache/crewai /app/docs_cache/search_index

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CACHE_TTL=3600
ENV MAX_CACHE_SIZE=104857600
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PATH=/mcp

# Use PORT environment variable (Smithery requirement)
ENV PORT=8000

# Expose port for HTTP transport
EXPOSE ${PORT}

# Run the MCP server in HTTP mode
CMD ["python", "main.py", "--transport", "http", "--host", "0.0.0.0", "--path", "/mcp"]