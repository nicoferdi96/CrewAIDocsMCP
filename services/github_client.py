"""GitHub API client for fetching CrewAI documentation."""

import os
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# GitHub configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
CREWAI_REPO = "crewAIInc/crewAI"
DOCS_PATH = "docs/en"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Optional, for higher rate limits

# Cache configuration
cache = {}
CACHE_TTL = timedelta(hours=1)


class GitHubDocsClient:
    """Client for fetching CrewAI documentation from GitHub"""
    
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CrewAI-MCP-Server"
        }
        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    async def fetch_file_content(self, path: str) -> Optional[str]:
        """Fetch raw content of a file from GitHub"""
        cache_key = f"file:{path}"
        
        # Check cache
        if cache_key in cache:
            cached_data, cached_time = cache[cache_key]
            if datetime.now() - cached_time < CACHE_TTL:
                return cached_data
        
        url = f"{GITHUB_RAW_BASE}/{CREWAI_REPO}/main/{path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    content = await response.text()
                    # Cache the result
                    cache[cache_key] = (content, datetime.now())
                    return content
                return None
    
    async def list_docs_files(self, subpath: str = "") -> List[Dict[str, Any]]:
        """List all files in a documentation directory"""
        cache_key = f"list:{subpath}"
        
        # Check cache
        if cache_key in cache:
            cached_data, cached_time = cache[cache_key]
            if datetime.now() - cached_time < CACHE_TTL:
                return cached_data
        
        path = f"{DOCS_PATH}/{subpath}".rstrip("/")
        url = f"{GITHUB_API_BASE}/repos/{CREWAI_REPO}/contents/{path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    files = await response.json()
                    # Cache the result
                    cache[cache_key] = (files, datetime.now())
                    return files
                return []
    
    async def get_all_doc_files(self) -> List[Dict[str, str]]:
        """Recursively get all documentation files"""
        all_files = []
        
        async def traverse_directory(path: str = ""):
            files = await self.list_docs_files(path)
            for file in files:
                if file["type"] == "file" and file["name"].endswith(".mdx"):
                    relative_path = file["path"].replace(f"{DOCS_PATH}/", "")
                    all_files.append({
                        "name": file["name"],
                        "path": file["path"],
                        "relative_path": relative_path,
                        "category": relative_path.split("/")[0] if "/" in relative_path else "root"
                    })
                elif file["type"] == "dir":
                    subpath = file["path"].replace(f"{DOCS_PATH}/", "")
                    await traverse_directory(subpath)
        
        await traverse_directory()
        return all_files