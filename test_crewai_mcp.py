import asyncio

from fastmcp import Client

async def test_server():
    """Test the CrewAI MCP server using streamable-http transport."""
    
    # Connect to the MCP server
    async with Client("http://localhost:8080/mcp") as client:
        print("🔗 Connected to CrewAI MCP server")
        
        # List available tools
        print("\n📋 Listing available tools...")
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> Tool found: {tool.name}")
        
        # Test search tool
        print("\n🔍 Testing search tool for 'flows'...")
        result = await client.call_tool("crewai/search-docs", {
            "query": "flows",
            "limit": 2
        })
        print(f"<<< Search result: {result[0].text[:200]}...")
        
        # Test get section tool
        print("\n📖 Testing get section tool for 'agents'...")
        result = await client.call_tool("crewai/get-section", {
            "section": "agents"
        })
        print(f"<<< Section result: {result[0].text[:200]}...")
        
        # Test list sections tool
        print("\n📚 Testing list sections tool...")
        result = await client.call_tool("crewai/list-sections", {})
        print(f"<<< Sections result: {result[0].text[:200]}...")
        
        # Test get examples tool
        print("\n💡 Testing get examples tool for 'agent'...")
        result = await client.call_tool("crewai/get-example", {
            "feature": "agent",
            "example_type": "basic"
        })
        print(f"<<< Examples result: {result[0].text[:200]}...")
        
        # Test API reference tool
        print("\n📋 Testing API reference tool for 'Agent' class...")
        result = await client.call_tool("crewai/get-api-reference", {
            "class_name": "Agent"
        })
        print(f"<<< API reference result: {result[0].text[:200]}...")
        
        print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_server())