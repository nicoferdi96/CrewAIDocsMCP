#!/usr/bin/env python3
"""
CrewAI Documentation MCP Server - HTTP Only

Provides intelligent access to CrewAI documentation through MCP tools.
Optimized for Smithery deployment with streamable HTTP transport.
"""

import os
from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from dotenv import load_dotenv

from services.documentation_service import DocumentationService
from services.cache_service import CacheService
from services.search_service import SearchService

# Load environment variables
load_dotenv()

# Initialize MCP server for HTTP transport only
mcp = FastMCP("crewai-docs")

# Initialize services
cache_service = CacheService(
    max_size=int(os.getenv("MAX_CACHE_SIZE", "104857600")),
    ttl=int(os.getenv("CACHE_TTL", "3600"))
)
doc_service = DocumentationService(cache_service)
search_service = SearchService()


@mcp.tool("crewai/search-docs")
async def search_docs(query: str, limit: int = 5) -> List[Dict]:
    """
    Search CrewAI documentation for relevant content.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 5)
        
    Returns:
        List of search results with relevance scores
    """
    try:
        results = await search_service.search(query, limit=limit)
        return [{
            "type": "search_results",
            "data": {
                "query": query,
                "results": results,
                "total": len(results)
            }
        }]
    except Exception as e:
        raise ToolError(f"Search failed: {str(e)}")


@mcp.tool("crewai/get-section")
async def get_section(section: str, subsection: Optional[str] = None) -> List[Dict]:
    """
    Get specific documentation section content.
    
    Available sections:
    - introduction: Getting started with CrewAI
    - agents: Agent configuration and customization
    - tasks: Task definition and management
    - tools: Built-in and custom tools
    - flows: Flow-based orchestration
    - crews: Crew composition and collaboration
    - memory: Memory systems and persistence
    - examples: Code examples and tutorials
    
    Args:
        section: Main section name
        subsection: Optional subsection within the main section
        
    Returns:
        Documentation content for the requested section
    """
    try:
        content = await doc_service.get_section(section, subsection)
        return [{
            "type": "section",
            "data": {
                "section": section,
                "subsection": subsection,
                "content": content
            }
        }]
    except Exception as e:
        raise ToolError(f"Failed to fetch section: {str(e)}")


@mcp.tool("crewai/get-example")
async def get_example(feature: str, example_type: str = "basic") -> List[Dict]:
    """
    Get code examples for specific CrewAI features.
    
    Features include:
    - agent: Agent creation and configuration
    - task: Task definition examples
    - tool: Custom tool implementation
    - crew: Crew setup and execution
    - flow: Flow-based workflows
    - memory: Memory integration examples
    
    Example types:
    - basic: Simple, minimal examples
    - advanced: Complex, real-world examples
    - integration: Examples showing integration with other systems
    
    Args:
        feature: Feature to get examples for
        example_type: Type of example (basic/advanced/integration)
        
    Returns:
        Code examples with explanations
    """
    try:
        examples = await doc_service.get_examples(feature, example_type)
        return [{
            "type": "example",
            "data": {
                "feature": feature,
                "example_type": example_type,
                "examples": examples
            }
        }]
    except Exception as e:
        raise ToolError(f"Failed to fetch examples: {str(e)}")


@mcp.tool("crewai/get-api-reference")
async def get_api_reference(class_name: str, method: Optional[str] = None) -> List[Dict]:
    """
    Get detailed API reference for CrewAI classes and methods.
    
    Common classes:
    - Agent: Core agent class
    - Task: Task definition class
    - Crew: Crew orchestration class
    - Flow: Flow control class
    - Tool: Base tool class
    
    Args:
        class_name: Name of the CrewAI class
        method: Optional specific method to get details for
        
    Returns:
        API documentation including parameters, return types, and examples
    """
    try:
        api_docs = await doc_service.get_api_reference(class_name, method)
        return [{
            "type": "api_reference",
            "data": {
                "class": class_name,
                "method": method,
                "documentation": api_docs
            }
        }]
    except Exception as e:
        raise ToolError(f"Failed to fetch API reference: {str(e)}")


@mcp.tool("crewai/list-sections")
async def list_sections() -> List[Dict]:
    """
    List all available documentation sections and their structure.
    
    Returns:
        Hierarchical list of all documentation sections
    """
    try:
        sections = await doc_service.list_sections()
        return [{
            "type": "sections",
            "data": {
                "sections": sections,
                "total": len(sections)
            }
        }]
    except Exception as e:
        raise ToolError(f"Failed to list sections: {str(e)}")


if __name__ == "__main__":
    # Get port from environment variable (Smithery sets this)
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting CrewAI Docs MCP server on port {port}...")
    print(f"Cache TTL: {os.getenv('CACHE_TTL', '3600')} seconds")
    print(f"Max cache size: {int(os.getenv('MAX_CACHE_SIZE', '104857600')) / 1024 / 1024:.2f} MB")
    
    # Run with streamable HTTP transport
    # Note: FastMCP should automatically use the PORT env variable
    mcp.run(transport="streamable-http")