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

# Expose port 8000 for HTTP transport
EXPOSE 8000

# Run the simplified MCP server
CMD ["python", "main.py"]