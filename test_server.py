#!/usr/bin/env python3
"""
Test script for CrewAI Docs MCP Server
"""

import json
import sys


def test_mcp_server():
    """Test basic MCP server functionality"""
    print("Testing CrewAI Docs MCP Server...")
    
    # Test importing all modules
    try:
        from services.cache_service import CacheService
        from services.documentation_service import DocumentationService
        from services.search_service import SearchService
        print("✓ All services imported successfully")
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test cache service
    try:
        cache = CacheService()
        cache.set("test", "value")
        assert cache.get("test") == "value"
        print("✓ Cache service working")
    except Exception as e:
        print(f"✗ Cache service error: {e}")
        return False
    
    # Test documentation service
    try:
        doc_service = DocumentationService(cache)
        print("✓ Documentation service initialized")
    except Exception as e:
        print(f"✗ Documentation service error: {e}")
        return False
    
    # Test search service
    try:
        search_service = SearchService()
        print("✓ Search service initialized")
    except Exception as e:
        print(f"✗ Search service error: {e}")
        return False
    
    print("\nAll tests passed! The server is ready to use.")
    print("\nTo run the server:")
    print("  python main.py")
    print("\nOr with MCP dev:")
    print("  mcp dev main.py")
    
    return True


if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)