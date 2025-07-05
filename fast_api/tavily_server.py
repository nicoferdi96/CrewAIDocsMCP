import os
from typing import Dict, List

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

load_dotenv()

if "TAVILY_API_KEY" not in os.environ:
    raise Exception("TAVILY_API_KEY environment variable not set")

# Tavily API key
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

# Initialize Tavily client
tavily_client = TavilyClient(TAVILY_API_KEY)

# Create an MCP server
mcp = FastMCP("web-search", stateless_http=True)


# Add a tool that uses Tavily
@mcp.tool()
def web_search(query: str) -> List[Dict]:
    """
    Use this tool to search the web for information.

    Args:
        query: The search query.

    Returns:
        The search results.
    """
    try:
        response = tavily_client.search(query)
        return response["results"]
    except:
        return "No results found"


# Run the server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
