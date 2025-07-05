"""
Documentation service for fetching and parsing CrewAI documentation from GitHub.
"""

import os
import re
import json
import httpx
from typing import Dict, List, Optional, Any
from pathlib import Path

from services.cache_service import CacheService


class DocumentationService:
    """
    Service for fetching, parsing, and caching CrewAI documentation from GitHub.
    """
    
    # GitHub base URL for raw content
    GITHUB_BASE = "https://raw.githubusercontent.com/crewAIInc/crewAI/main/docs/en"
    
    # Complete documentation structure from CrewAI GitHub
    DOCUMENTATION_MAP = {
        # Core concepts
        "agents": "/concepts/agents.mdx",
        "tasks": "/concepts/tasks.mdx",
        "crews": "/concepts/crews.mdx",
        "flows": "/concepts/flows.mdx",
        "tools": "/concepts/tools.mdx",
        "memory": "/concepts/memory.mdx",
        "knowledge": "/concepts/knowledge.mdx",
        "llms": "/concepts/llms.mdx",
        "cli": "/concepts/cli.mdx",
        "testing": "/concepts/testing.mdx",
        "training": "/concepts/training.mdx",
        "environments": "/concepts/environments.mdx",
        
        # Getting started
        "introduction": "/introduction.mdx",
        "quickstart": "/quickstart.mdx",
        "installation": "/installation.mdx",
        
        # Guides
        "create-new-tool": "/guides/create-new-tool.mdx",
        "llm-connections": "/guides/llm-connections.mdx",
        "browserbasecloud": "/guides/browserbasecloud.mdx",
        "agentops": "/guides/agentops.mdx",
        "langtrace": "/guides/langtrace.mdx"
    }
    
    def __init__(self, cache_service: CacheService):
        """
        Initialize documentation service.
        
        Args:
            cache_service: Cache service instance
        """
        self.cache = cache_service
        self.client = None
        self.docs_cache_dir = Path("docs_cache/crewai")
        self.docs_cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def _ensure_client(self):
        """Ensure httpx client is created."""
        if self.client is None:
            self.client = httpx.AsyncClient()
            
    async def _fetch_from_github(self, path: str) -> str:
        """
        Fetch documentation content from GitHub.
        
        Args:
            path: Path to the MDX file
            
        Returns:
            Raw MDX content
        """
        await self._ensure_client()
        
        # Check cache first
        cache_key = f"github:{path}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        url = f"{self.GITHUB_BASE}{path}"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                content = response.text
                self.cache.set(cache_key, content)
                
                # Also save to local file cache
                local_file = self.docs_cache_dir / path.lstrip('/').replace('/', '_')
                local_file.write_text(content)
                
                return content
            else:
                raise Exception(f"GitHub returned {response.status_code} for {path}")
                    
        except Exception as e:
            # Try local cache if GitHub fails
            local_file = self.docs_cache_dir / path.lstrip('/').replace('/', '_')
            if local_file.exists():
                return local_file.read_text()
            raise Exception(f"Failed to fetch {path}: {str(e)}")
            
    def _parse_mdx_content(self, content: str) -> Dict[str, Any]:
        """
        Parse MDX content to extract structured documentation.
        
        Args:
            content: Raw MDX content
            
        Returns:
            Parsed documentation structure
        """
        result = {
            "frontmatter": {},
            "title": "",
            "description": "",
            "sections": [],
            "code_examples": [],
            "content": content
        }
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            # Simple frontmatter parsing
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    result["frontmatter"][key.strip()] = value.strip().strip('"')
            
            # Remove frontmatter from content
            content = content[frontmatter_match.end():]
            
            # Extract title and description from frontmatter
            result["title"] = result["frontmatter"].get("title", "")
            result["description"] = result["frontmatter"].get("description", "")
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        for lang, code in code_blocks:
            result["code_examples"].append({
                "language": lang or "python",
                "code": code.strip()
            })
        
        # Extract section headers
        sections = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        for level, title in sections:
            result["sections"].append({
                "level": len(level),
                "title": title.strip()
            })
        
        return result
            
    async def get_section(self, section: str, subsection: Optional[str] = None) -> Dict[str, Any]:
        """
        Get documentation for a specific section.
        
        Args:
            section: Main section name
            subsection: Optional subsection
            
        Returns:
            Parsed documentation content
        """
        if section not in self.DOCUMENTATION_MAP:
            # Try to find a partial match
            for key in self.DOCUMENTATION_MAP:
                if section.lower() in key.lower():
                    section = key
                    break
            else:
                raise ValueError(f"Unknown section: {section}. Available sections: {list(self.DOCUMENTATION_MAP.keys())}")
            
        path = self.DOCUMENTATION_MAP[section]
        content = await self._fetch_from_github(path)
        parsed = self._parse_mdx_content(content)
        
        # Add section info
        parsed["section"] = section
        parsed["path"] = path
        parsed["url"] = f"https://docs.crewai.com/en/{path.lstrip('/')}"
        
        return parsed
        
    async def get_examples(self, feature: str, example_type: str = "basic") -> List[Dict[str, Any]]:
        """
        Get code examples for a feature from the documentation.
        
        Args:
            feature: Feature name (e.g., "agent", "task", "flow")
            example_type: Type of examples (basic/advanced/integration)
            
        Returns:
            List of code examples
        """
        # Map feature to section
        feature_map = {
            "agent": "agents",
            "task": "tasks",
            "crew": "crews",
            "flow": "flows",
            "tool": "tools",
            "memory": "memory"
        }
        
        section = feature_map.get(feature, feature)
        doc = await self.get_section(section)
        
        # Extract relevant code examples
        examples = []
        for code_block in doc.get("code_examples", []):
            if code_block.get("language") in ["python", "py"]:
                examples.append({
                    "title": f"{feature.title()} Example",
                    "description": f"Example of {feature} implementation",
                    "code": code_block["code"],
                    "language": "python"
                })
        
        return examples
        
    async def get_api_reference(self, class_name: str, method: Optional[str] = None) -> Dict[str, Any]:
        """
        Get API reference documentation for a class.
        
        Args:
            class_name: Name of the CrewAI class
            method: Optional specific method
            
        Returns:
            API documentation
        """
        # Map class names to sections
        class_map = {
            "Agent": "agents",
            "Task": "tasks",
            "Crew": "crews",
            "Flow": "flows",
            "Tool": "tools"
        }
        
        section = class_map.get(class_name, class_name.lower())
        doc = await self.get_section(section)
        
        # Extract API information from the documentation
        api_info = {
            "class": class_name,
            "description": doc.get("description", ""),
            "section": section,
            "methods": [],
            "attributes": [],
            "examples": doc.get("code_examples", [])
        }
        
        # Parse content for method signatures and attributes
        content = doc.get("content", "")
        
        # Look for method definitions (simplified parsing)
        method_patterns = [
            r'`\.(\w+)\((.*?)\)`',  # `.method(args)`
            r'`(\w+)\((.*?)\)`',     # `method(args)`
            r'- `(\w+)\((.*?)\)`',   # - `method(args)`
        ]
        
        for pattern in method_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                method_name = match[0]
                if method and method != method_name:
                    continue
                api_info["methods"].append({
                    "name": method_name,
                    "signature": f"{method_name}({match[1]})"
                })
        
        return api_info
        
    async def list_sections(self) -> List[Dict[str, Any]]:
        """
        List all available documentation sections.
        
        Returns:
            List of sections with metadata
        """
        sections = []
        
        # Group sections by category
        categories = {
            "Getting Started": ["introduction", "quickstart", "installation"],
            "Core Concepts": ["agents", "tasks", "crews", "flows", "tools", "memory", "knowledge", "llms"],
            "Advanced": ["testing", "training", "environments", "cli"],
            "Guides": ["create-new-tool", "llm-connections", "browserbasecloud", "agentops", "langtrace"]
        }
        
        for category, section_list in categories.items():
            for section_name in section_list:
                if section_name in self.DOCUMENTATION_MAP:
                    sections.append({
                        "name": section_name,
                        "category": category,
                        "title": section_name.replace("-", " ").title(),
                        "path": self.DOCUMENTATION_MAP[section_name],
                        "url": f"https://docs.crewai.com/en{self.DOCUMENTATION_MAP[section_name].rstrip('.mdx')}"
                    })
        
        return sections
        
    async def search_documentation(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search through all documentation.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Search results
        """
        results = []
        query_lower = query.lower()
        
        # Search through all sections
        for section_name, path in self.DOCUMENTATION_MAP.items():
            try:
                content = await self._fetch_from_github(path)
                content_lower = content.lower()
                
                # Simple relevance scoring
                score = 0
                if query_lower in section_name:
                    score += 10
                if query_lower in content_lower:
                    score += content_lower.count(query_lower)
                
                if score > 0:
                    parsed = self._parse_mdx_content(content)
                    
                    # Find context around the query
                    context_start = max(0, content_lower.find(query_lower) - 100)
                    context_end = min(len(content), context_start + 200 + len(query))
                    context = content[context_start:context_end].strip()
                    if context_start > 0:
                        context = "..." + context
                    if context_end < len(content):
                        context = context + "..."
                    
                    results.append({
                        "section": section_name,
                        "title": parsed.get("title", section_name.title()),
                        "score": score,
                        "context": context,
                        "path": path
                    })
            except Exception as e:
                # Skip sections that fail to load
                continue
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
            
    async def close(self):
        """Close the httpx client."""
        if self.client:
            await self.client.aclose()