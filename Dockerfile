FROM python:3.11-slim as builder

# Install UV
RUN pip install uv

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./

# Build wheel using UV
RUN uv pip install --system build && \
    python -m build --wheel

FROM python:3.11-slim

WORKDIR /app

# Install UV in final image
RUN pip install uv

# Copy built wheels and project files
COPY --from=builder /app/dist /app/dist
COPY . .

# Install dependencies with UV
RUN uv pip install --system --no-cache /app/dist/*.whl && \
    groupadd -r mcp && \
    useradd -r -g mcp -d /app -s /bin/bash mcp && \
    chown -R mcp:mcp /app

# Create necessary directories
RUN mkdir -p /app/docs_cache/crewai /app/docs_cache/search_index && \
    chown -R mcp:mcp /app/docs_cache

USER mcp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CACHE_TTL=3600
ENV MAX_CACHE_SIZE=104857600
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV MCP_PATH=/mcp

# Expose port for HTTP transport
EXPOSE 8000

# Run the MCP server in HTTP mode
CMD ["python", "main.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8000", "--path", "/mcp"]