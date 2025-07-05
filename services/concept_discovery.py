"""Dynamic concept discovery service for CrewAI documentation."""

from typing import Dict, List

from .github_client import DOCS_PATH, GitHubDocsClient


class ConceptDiscoveryService:
    """Service for automatically discovering available CrewAI concepts."""

    def __init__(self, github_client: GitHubDocsClient):
        self.github_client = github_client
        self._cached_concepts = None

    async def discover_concepts(self) -> Dict[str, str]:
        """
        Dynamically discover available concept files.

        Returns:
            Dictionary mapping concept names to their relative file paths
        """
        # Return cached result if available
        if self._cached_concepts is not None:
            return self._cached_concepts

        try:
            concept_files = await self.github_client.list_docs_files("concepts")
            concept_map = {}

            for file in concept_files:
                if file["type"] == "file" and file["name"].endswith(".mdx"):
                    # Extract concept name from filename (e.g., "agents.mdx" -> "agents")
                    concept_name = file["name"].replace(".mdx", "").lower()
                    relative_path = file["path"].replace(f"{DOCS_PATH}/", "")
                    concept_map[concept_name] = relative_path

            # Cache the result
            self._cached_concepts = concept_map
            return concept_map

        except Exception as e:
            print(f"⚠️ Failed to discover concepts: {e}")
            # Fallback to basic concepts if discovery fails
            fallback = {
                "agents": "concepts/agents.mdx",
                "tasks": "concepts/tasks.mdx",
                "crews": "concepts/crews.mdx",
                "tools": "concepts/tools.mdx",
                "memory": "concepts/memory.mdx",
            }
            self._cached_concepts = fallback
            return fallback

    async def get_concept_info(self, concept_name: str) -> Dict[str, any]:
        """
        Get information about a specific concept.

        Args:
            concept_name: Name of the concept to lookup

        Returns:
            Dictionary with concept information or error
        """
        concept_map = await self.discover_concepts()

        if concept_name.lower() not in concept_map:
            return {
                "error": f"Concept '{concept_name}' not found",
                "available_concepts": list(concept_map.keys()),
                "suggestion": self._suggest_similar_concept(
                    concept_name, concept_map.keys()
                ),
            }

        file_path = concept_map[concept_name.lower()]
        return {
            "concept": concept_name,
            "file_path": file_path,
            "full_path": f"{DOCS_PATH}/{file_path}",
        }

    def _suggest_similar_concept(
        self, query: str, available_concepts: List[str]
    ) -> str:
        """
        Suggest a similar concept name based on string similarity.

        Args:
            query: The concept name that wasn't found
            available_concepts: List of available concept names

        Returns:
            Most similar concept name
        """
        if not available_concepts:
            return ""

        # Simple similarity based on common prefixes and substrings
        query_lower = query.lower()

        # First, try exact substring matches
        for concept in available_concepts:
            if query_lower in concept or concept in query_lower:
                return concept

        # Then try common prefixes
        best_match = available_concepts[0]
        best_score = 0

        for concept in available_concepts:
            # Calculate simple similarity score
            common_chars = sum(1 for a, b in zip(query_lower, concept) if a == b)
            score = common_chars / max(len(query_lower), len(concept))

            if score > best_score:
                best_score = score
                best_match = concept

        return best_match

    async def list_all_concepts(self) -> Dict[str, any]:
        """
        List all available concepts with their file paths.

        Returns:
            Dictionary with concept information
        """
        concept_map = await self.discover_concepts()

        return {
            "total_concepts": len(concept_map),
            "concepts": list(concept_map.keys()),
            "concept_files": concept_map,
        }

    def clear_cache(self):
        """Clear the concept discovery cache to force re-discovery."""
        self._cached_concepts = None
