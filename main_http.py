#!/usr/bin/env python3
"""
CrewAI Documentation MCP Server - HTTP Mode

Entry point for production deployment using HTTP transport.
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Run main.py with HTTP transport using environment variables or defaults
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = os.getenv("MCP_PORT", "8000")
    path = os.getenv("MCP_PATH", "/mcp")
    
    cmd = [
        sys.executable, "main.py", 
        "--transport", "http", 
        "--host", host, 
        "--port", port, 
        "--path", path
    ]
    subprocess.run(cmd)