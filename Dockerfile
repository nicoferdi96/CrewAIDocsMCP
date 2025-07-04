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

# Expose port for HTTP transport (Smithery will set PORT env var)
EXPOSE 8000

# Run the MCP server
CMD ["python", "main.py"]