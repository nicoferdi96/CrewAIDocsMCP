#!/usr/bin/env python3
"""
CrewAI Documentation MCP Server - Stdio Mode

Entry point for local development using stdio transport.
"""

import subprocess
import sys

if __name__ == "__main__":
    # Run main.py with stdio transport
    cmd = [sys.executable, "main.py", "--transport", "stdio"]
    subprocess.run(cmd)