"""CrewAI Documentation MCP Server - Clean implementation with Whoosh search."""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

from services.concept_discovery import ConceptDiscoveryService
from services.github_client import DOCS_PATH, GitHubDocsClient
from services.vector_search import VectorSearch
from utils.doc_parser import extract_code_blocks, extract_sections

# Initialize services
github_client = GitHubDocsClient()
search_service = VectorSearch()
concept_service = ConceptDiscoveryService(github_client)

# Create MCP server
mcp = FastMCP("crewai-docs", stateless_http=True, port=10001)


# MCP Tools


@mcp.tool()
async def get_search_status() -> Dict[str, Any]:
    """
    Get the current status of the search index.

    Returns:
        Status information about the search indexing process
    """
    return search_service.get_status()


@mcp.tool()
async def search_crewai_docs(
    query: str, category: Optional[str] = None, limit: int = 10
) -> Dict[str, Any]:
    """
    Search CrewAI documentation using AI-powered semantic search with OpenAI embeddings.

    Args:
        query: Natural language search query (e.g., "How do I create an agent?", "workflow automation")
        category: Optional category filter (e.g., "concepts", "guides", "examples")
        limit: Maximum number of results to return (default: 10)

    Returns:
        Dictionary with semantically relevant search results and metadata
    """
    # Ensure search service is initialized
    if not search_service._ready:
        await search_service.initialize()

    return await search_service.search(query, category, limit)


@mcp.tool()
async def list_available_concepts() -> Dict[str, Any]:
    """
    List all available CrewAI concepts that can be retrieved.

    Returns:
        Dictionary with available concepts and their file paths
    """
    return await concept_service.list_all_concepts()


@mcp.tool()
async def get_concept_docs(concept: str) -> Dict[str, Any]:
    """
    Get comprehensive documentation for a specific CrewAI concept.

    Args:
        concept: The concept to retrieve (e.g., "agents", "tasks", "crews")

    Returns:
        Full documentation content for the concept with parsed sections
    """
    # Get concept information
    concept_info = await concept_service.get_concept_info(concept)

    if "error" in concept_info:
        return concept_info

    # Fetch the actual content
    try:
        content = await github_client.fetch_file_content(concept_info["full_path"])
        if not content:
            return {"error": f"Could not fetch content for concept: {concept}"}

        return {
            "concept": concept_info["concept"],
            "file_path": concept_info["file_path"],
            "content": content,
            "sections": extract_sections(content),
            "code_blocks": extract_code_blocks(content),
        }

    except Exception as e:
        return {"error": f"Error fetching concept documentation: {str(e)}"}


@mcp.tool()
async def get_code_examples(feature: str, limit: int = 10) -> Dict[str, Any]:
    """
    Extract code examples for a specific CrewAI feature using advanced search.

    Args:
        feature: The feature to get examples for (e.g., "agent creation", "tool usage")
        limit: Maximum number of examples to return

    Returns:
        Dictionary with code examples and source information
    """
    # Search for the feature
    search_results = search_service.search(
        feature, limit=limit * 2
    )  # Get more to filter

    if search_results["status"] != "ready":
        return {
            "status": search_results["status"],
            "message": search_results.get("message", "Search not ready"),
            "examples": [],
        }

    all_examples = []

    # Extract code examples from search results
    for result in search_results["results"]:
        try:
            # Get full content for code extraction
            full_content = await github_client.fetch_file_content(
                f"{DOCS_PATH}/{result['path']}"
            )
            if full_content:
                examples = extract_code_blocks(full_content)

                for example in examples:
                    all_examples.append(
                        {
                            "source": result["title"],
                            "category": result["category"],
                            "file_path": result["path"],
                            "code": example["code"],
                            "language": example["language"],
                            "description": example.get("description", ""),
                            "relevance_score": result["score"],
                        }
                    )

                    if len(all_examples) >= limit:
                        break

        except Exception as e:
            print(f"Error extracting examples from {result['path']}: {e}")
            continue

    return {
        "status": "ready",
        "feature": feature,
        "total_examples": len(all_examples),
        "examples": all_examples[:limit],
    }


@mcp.tool()
async def get_doc_file(file_path: str) -> Dict[str, Any]:
    """
    Retrieve the full content of a specific documentation file.

    Args:
        file_path: Relative path to the doc file (e.g., "concepts/agents.mdx")

    Returns:
        Full content and parsed metadata of the documentation file
    """
    try:
        full_path = f"{DOCS_PATH}/{file_path}"
        content = await github_client.fetch_file_content(full_path)

        if not content:
            return {"error": f"Could not fetch documentation file: {file_path}"}

        return {
            "file_path": file_path,
            "content": content,
            "sections": extract_sections(content),
            "code_blocks": extract_code_blocks(content),
        }

    except Exception as e:
        return {"error": f"Error fetching file: {str(e)}"}


@mcp.tool()
async def refresh_search_index() -> Dict[str, Any]:
    """
    Force refresh of the vector search index to get latest documentation.

    Note: This will re-embed all documents using OpenAI's API, which may take a few minutes.
    The index normally refreshes automatically once per day.

    Returns:
        Status of the refresh operation
    """
    try:
        # Clear concept cache
        concept_service.clear_cache()

        # Start background indexing
        await search_service.start_background_indexing()

        return {
            "status": "started",
            "message": "Vector index refresh started in background. This may take a few minutes.",
            "embedding_model": search_service.model,
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to refresh index: {str(e)}"}


# Create a background task to initialize services
async def initialize_services():
    """Initialize services in background."""
    try:
        print("🚀 Starting CrewAI Docs MCP Server...")
        print("📚 Initializing search service...")
        await search_service.initialize()
        print("✅ Search service initialization complete!")

        # Pre-populate concept cache
        print("📂 Loading concept cache...")
        await concept_service.list_all_concepts()
        print("✅ Concept cache populated!")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")


# Run the server standalone
if __name__ == "__main__":
    # Start initialization in background using asyncio
    def start_background_init():
        """Start background initialization."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_services())
        loop.close()

    # Start initialization in a separate thread to not block server startup
    import threading

    init_thread = threading.Thread(target=start_background_init, daemon=True)
    init_thread.start()

    mcp.run(transport="streamable-http")
