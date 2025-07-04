"""
Documentation service for fetching and parsing CrewAI documentation.
"""

import os
import json
import aiohttp
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from pathlib import Path

from services.cache_service import CacheService


class DocumentationService:
    """
    Service for fetching, parsing, and caching CrewAI documentation.
    """
    
    # CrewAI documentation structure
    SECTIONS = {
        "introduction": {
            "url": "https://docs.crewai.com/introduction",
            "subsections": ["overview", "installation", "quickstart"]
        },
        "agents": {
            "url": "https://docs.crewai.com/core-concepts/agents",
            "subsections": ["creating-agents", "agent-attributes", "agent-tools"]
        },
        "tasks": {
            "url": "https://docs.crewai.com/core-concepts/tasks",
            "subsections": ["task-attributes", "task-output", "conditional-tasks"]
        },
        "tools": {
            "url": "https://docs.crewai.com/core-concepts/tools",
            "subsections": ["using-crewai-tools", "using-langchain-tools", "custom-tools"]
        },
        "crews": {
            "url": "https://docs.crewai.com/core-concepts/crews",
            "subsections": ["crew-attributes", "crew-output", "hierarchical-process"]
        },
        "flows": {
            "url": "https://docs.crewai.com/core-concepts/flows",
            "subsections": ["flow-basics", "flow-state", "conditional-flows"]
        },
        "memory": {
            "url": "https://docs.crewai.com/core-concepts/memory",
            "subsections": ["short-term-memory", "long-term-memory", "entity-memory"]
        },
        "examples": {
            "url": "https://docs.crewai.com/examples",
            "subsections": ["basic-examples", "advanced-examples", "real-world-applications"]
        }
    }
    
    # API reference classes
    API_CLASSES = {
        "Agent": {
            "methods": ["execute", "set_tools", "get_context"],
            "attributes": ["role", "goal", "backstory", "tools", "llm"]
        },
        "Task": {
            "methods": ["execute", "get_output"],
            "attributes": ["description", "expected_output", "agent", "tools"]
        },
        "Crew": {
            "methods": ["kickoff", "train", "replay"],
            "attributes": ["agents", "tasks", "process", "memory"]
        },
        "Flow": {
            "methods": ["start", "add_step", "run"],
            "attributes": ["state", "steps", "conditions"]
        },
        "Tool": {
            "methods": ["run", "validate_input"],
            "attributes": ["name", "description", "func"]
        }
    }
    
    def __init__(self, cache_service: CacheService):
        """
        Initialize documentation service.
        
        Args:
            cache_service: Cache service instance
        """
        self.cache = cache_service
        self.session = None
        self.docs_cache_dir = Path("docs_cache/crewai")
        self.docs_cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
    async def _fetch_url(self, url: str) -> str:
        """
        Fetch content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content
        """
        await self._ensure_session()
        
        # Check cache first
        cached = self.cache.get(f"url:{url}")
        if cached:
            return cached
            
        try:
            async with self.session.get(url) as response:
                content = await response.text()
                self.cache.set(f"url:{url}", content)
                return content
        except Exception as e:
            # Try local cache if available
            local_file = self.docs_cache_dir / f"{url.replace('/', '_')}.html"
            if local_file.exists():
                return local_file.read_text()
            raise Exception(f"Failed to fetch {url}: {str(e)}")
            
    async def get_section(self, section: str, subsection: Optional[str] = None) -> Dict[str, Any]:
        """
        Get documentation for a specific section.
        
        Args:
            section: Main section name
            subsection: Optional subsection
            
        Returns:
            Parsed documentation content
        """
        cache_key = f"section:{section}:{subsection or 'main'}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        if section not in self.SECTIONS:
            raise ValueError(f"Unknown section: {section}")
            
        section_info = self.SECTIONS[section]
        url = section_info["url"]
        
        if subsection:
            # Construct subsection URL (this is a simplified approach)
            url = f"{url}/{subsection}"
            
        # For now, return structured placeholder data
        # In production, this would fetch and parse actual documentation
        content = {
            "title": f"{section.title()}{f' - {subsection.title()}' if subsection else ''}",
            "description": f"Documentation for {section}{f' ({subsection})' if subsection else ''}",
            "url": url,
            "content": self._get_placeholder_content(section, subsection),
            "subsections": section_info.get("subsections", []) if not subsection else []
        }
        
        self.cache.set(cache_key, content)
        return content
        
    async def get_examples(self, feature: str, example_type: str = "basic") -> List[Dict[str, Any]]:
        """
        Get code examples for a feature.
        
        Args:
            feature: Feature name
            example_type: Type of examples
            
        Returns:
            List of examples
        """
        cache_key = f"examples:{feature}:{example_type}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        # Return placeholder examples
        examples = self._get_placeholder_examples(feature, example_type)
        self.cache.set(cache_key, examples)
        return examples
        
    async def get_api_reference(self, class_name: str, method: Optional[str] = None) -> Dict[str, Any]:
        """
        Get API reference documentation.
        
        Args:
            class_name: Class name
            method: Optional method name
            
        Returns:
            API documentation
        """
        cache_key = f"api:{class_name}:{method or 'class'}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        if class_name not in self.API_CLASSES:
            raise ValueError(f"Unknown class: {class_name}")
            
        class_info = self.API_CLASSES[class_name]
        
        if method and method not in class_info["methods"]:
            raise ValueError(f"Unknown method: {class_name}.{method}")
            
        # Return structured API documentation
        api_doc = self._get_placeholder_api_doc(class_name, method, class_info)
        self.cache.set(cache_key, api_doc)
        return api_doc
        
    async def list_sections(self) -> List[Dict[str, Any]]:
        """
        List all available documentation sections.
        
        Returns:
            List of sections with metadata
        """
        sections = []
        for name, info in self.SECTIONS.items():
            sections.append({
                "name": name,
                "title": name.replace("_", " ").title(),
                "url": info["url"],
                "subsections": info.get("subsections", [])
            })
        return sections
        
    def _get_placeholder_content(self, section: str, subsection: Optional[str]) -> str:
        """Get placeholder content for a section."""
        if section == "agents":
            if subsection == "creating-agents":
                return """
# Creating Agents

Agents are the building blocks of CrewAI. Each agent has a specific role, goal, and backstory.

## Basic Agent Creation

```python
from crewai import Agent

researcher = Agent(
    role='Senior Research Analyst',
    goal='Uncover cutting-edge developments in AI',
    backstory='You are an expert analyst with deep knowledge of AI trends',
    verbose=True,
    allow_delegation=False
)
```

## Agent Attributes

- **role**: Defines the agent's function within the crew
- **goal**: The objective the agent aims to achieve
- **backstory**: Provides context to guide the agent's behavior
- **tools**: List of tools available to the agent
- **verbose**: Enable detailed logging
- **allow_delegation**: Whether the agent can delegate tasks
"""
            elif subsection == "agent-tools":
                return """
# Agent Tools

Agents can use various tools to accomplish their tasks.

## Assigning Tools

```python
from crewai_tools import SerperDevTool, WebsiteSearchTool

search_tool = SerperDevTool()
web_tool = WebsiteSearchTool()

agent = Agent(
    role='Research Analyst',
    goal='Find accurate information',
    tools=[search_tool, web_tool]
)
```
"""
        elif section == "tasks":
            return """
# Tasks in CrewAI

Tasks define the specific work that agents need to accomplish.

## Task Definition

```python
from crewai import Task

research_task = Task(
    description='Research the latest AI trends in 2024',
    expected_output='A comprehensive report on AI trends',
    agent=researcher
)
```
"""
        elif section == "crews":
            return """
# Crews

Crews orchestrate multiple agents working together.

## Creating a Crew

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential
)

result = crew.kickoff()
```
"""
        return f"Documentation content for {section}{f' - {subsection}' if subsection else ''}"
        
    def _get_placeholder_examples(self, feature: str, example_type: str) -> List[Dict[str, Any]]:
        """Get placeholder examples."""
        examples = []
        
        if feature == "agent" and example_type == "basic":
            examples.append({
                "title": "Basic Agent Example",
                "description": "Creating a simple research agent",
                "code": """from crewai import Agent

researcher = Agent(
    role='Senior Researcher',
    goal='Conduct thorough research on given topics',
    backstory='You are an experienced researcher with a keen eye for detail',
    verbose=True
)""",
                "language": "python"
            })
        elif feature == "crew" and example_type == "basic":
            examples.append({
                "title": "Basic Crew Example",
                "description": "Setting up a simple crew with two agents",
                "code": """from crewai import Crew, Agent, Task, Process

# Create agents
researcher = Agent(
    role='Researcher',
    goal='Research topics thoroughly'
)

writer = Agent(
    role='Writer',
    goal='Write compelling content'
)

# Create tasks
research_task = Task(
    description='Research AI trends',
    agent=researcher
)

write_task = Task(
    description='Write article about AI trends',
    agent=writer
)

# Create crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential
)

# Execute
result = crew.kickoff()""",
                "language": "python"
            })
            
        return examples
        
    def _get_placeholder_api_doc(self, class_name: str, method: Optional[str], class_info: Dict) -> Dict[str, Any]:
        """Get placeholder API documentation."""
        if method:
            return {
                "class": class_name,
                "method": method,
                "signature": f"{method}(self, *args, **kwargs)",
                "description": f"Execute {method} on {class_name}",
                "parameters": [
                    {"name": "args", "type": "Any", "description": "Positional arguments"},
                    {"name": "kwargs", "type": "Any", "description": "Keyword arguments"}
                ],
                "returns": {"type": "Any", "description": "Method result"},
                "example": f"instance.{method}()"
            }
        else:
            return {
                "class": class_name,
                "description": f"{class_name} class for CrewAI",
                "methods": class_info["methods"],
                "attributes": class_info["attributes"],
                "example": f"{class_name.lower()} = {class_name}(...)"
            }
            
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()