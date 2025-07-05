"""Simple vector search service following OpenAI guidelines."""

import asyncio
import logging
import os

# Import MDX parser components
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from openai import AsyncOpenAI

from .github_client import GitHubDocsClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.mdx_parser import MDXParser, SemanticChunker


class VectorSearch:
    """Simple vector search following OpenAI guidelines."""

    def __init__(self, data_dir: str = "./vector_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # OpenAI setup
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"

        # Data
        self.df: Optional[pd.DataFrame] = None
        self.github_client = GitHubDocsClient()

        # State
        self._ready = False
        self._indexing_task: Optional[asyncio.Task] = None

        # Parsers and chunkers
        self.mdx_parser = MDXParser()
        self.semantic_chunker = SemanticChunker(
            target_chunk_size=600,  # words
            max_chunk_size=1000,  # words
            overlap_size=50,  # words
        )

    async def initialize(self):
        """Initialize the search service."""
        try:
            csv_path = self.data_dir / "embeddings.csv"

            if csv_path.exists() and not await self._should_rebuild():
                print("📚 Loading existing embeddings...")
                await self._load_embeddings()
                self._ready = True
                print(f"✅ Loaded {len(self.df)} document chunks")
            else:
                print("🏗️ Building new embeddings...")
                await self.start_background_indexing()

        except Exception as e:
            print(f"⚠️ Error initializing: {e}")
            await self.start_background_indexing()

    async def start_background_indexing(self):
        """Start background indexing."""
        if self._indexing_task is None or self._indexing_task.done():
            self._indexing_task = asyncio.create_task(self._build_embeddings())

    async def _build_embeddings(self):
        """Build embeddings following OpenAI guidelines."""
        try:
            print("🔄 Fetching documentation...")

            # Get all docs
            files = await self.github_client.get_all_doc_files()

            # Process into semantic chunks
            chunks_data = []
            for file_info in files:
                try:
                    content = await self.github_client.fetch_file_content(
                        file_info["path"]
                    )
                    if content:
                        # Parse MDX document
                        document = self.mdx_parser.parse(
                            content, file_info["relative_path"]
                        )

                        # Create semantic chunks
                        file_chunks = self.semantic_chunker.chunk_document(
                            document, file_info["relative_path"]
                        )

                        # Add to chunks data
                        chunks_data.extend(file_chunks)

                        print(
                            f"📄 {file_info['name']}: {len(file_chunks)} semantic chunks"
                        )

                except Exception as e:
                    print(f"⚠️ Failed to process {file_info['path']}: {e}")
                    continue

            print(f"📊 Created {len(chunks_data)} chunks from {len(files)} documents")

            # Create DataFrame
            df = pd.DataFrame(chunks_data)

            # Generate embeddings
            print("🧮 Generating embeddings...")
            embeddings = []
            batch_size = 100

            for i in range(0, len(df), batch_size):
                batch = df.iloc[i : i + batch_size]
                batch_texts = batch["combined"].tolist()

                response = await self.client.embeddings.create(
                    model=self.model, input=batch_texts
                )

                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                print(f"   Embedded {i + len(batch)}/{len(df)} chunks...")

            # Add embeddings to DataFrame
            df["embedding"] = embeddings

            # Save to CSV
            csv_path = self.data_dir / "embeddings.csv"
            df.to_csv(csv_path, index=False)

            # Create timestamp file
            timestamp_path = self.data_dir / ".last_build"
            timestamp_path.touch()

            # Set data
            self.df = df
            self._ready = True

            print(f"✅ Embeddings complete! Saved {len(df)} chunks to {csv_path}")

        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            logging.error(f"Embedding error: {e}", exc_info=True)
            self._ready = False

    async def _load_embeddings(self):
        """Load embeddings from CSV."""
        csv_path = self.data_dir / "embeddings.csv"

        # Load DataFrame
        df = pd.read_csv(csv_path)

        # Convert embedding strings back to arrays
        df["embedding"] = df["embedding"].apply(eval).apply(np.array)

        self.df = df
        print(f"📂 Loaded {len(df)} embeddings from {csv_path}")

    async def _should_rebuild(self) -> bool:
        """Check if embeddings should be rebuilt."""
        timestamp_path = self.data_dir / ".last_build"

        if not timestamp_path.exists():
            return True

        # Check if older than 24 hours
        last_build = datetime.fromtimestamp(timestamp_path.stat().st_mtime)
        return datetime.now() - last_build > timedelta(days=1)

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text following OpenAI guidelines."""
        text = text.replace("\\n", " ")
        response = await self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def search(
        self, query: str, category: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """Search using cosine similarity following OpenAI guidelines."""
        if not self._ready or self.df is None:
            return {
                "status": "indexing",
                "message": "Embeddings are being built. Please try again in a moment.",
                "results": [],
            }

        try:
            print(f"🔍 Searching for: '{query}'")

            # Get query embedding
            query_embedding = np.array(await self.get_embedding(query))

            # Calculate similarities
            df = self.df.copy()
            df["similarity"] = df["embedding"].apply(
                lambda x: self.cosine_similarity(x, query_embedding)
            )

            # Filter by category if specified
            if category:
                df = df[df["category"] == category]

            # Sort by similarity and get top results
            results_df = df.sort_values("similarity", ascending=False).head(limit)

            # Format results with enhanced metadata
            results = []
            for _, row in results_df.iterrows():
                results.append(
                    {
                        "path": row["path"],
                        "title": row["title"],
                        "category": row["category"],
                        "score": float(row["similarity"]),
                        "snippet": row["content"][:200] + "..."
                        if len(row["content"]) > 200
                        else row["content"],
                        "concepts": [],
                        # Enhanced metadata from semantic chunking
                        "chunk_type": row.get("chunk_type", "content"),
                        "section_hierarchy": row.get("section_hierarchy", ""),
                        "heading_level": row.get("heading_level", 0),
                        "word_count": row.get("word_count", 0),
                        "has_code_blocks": row.get("has_code_blocks", False),
                        "has_special_components": row.get(
                            "has_special_components", False
                        ),
                    }
                )

            print(f"🔍 Found {len(results)} relevant documents")

            return {
                "status": "ready",
                "query": query,
                "category_filter": category,
                "total_found": len(results),
                "total_docs": len(self.df["path"].unique())
                if self.df is not None
                else 0,
                "results": results,
            }

        except Exception as e:
            print(f"⚠️ Search error: {e}")
            logging.error(f"Search error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Search error: {str(e)}",
                "results": [],
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        if self._ready and self.df is not None:
            return {
                "status": "ready",
                "message": f"Embeddings ready with {len(self.df)} chunks from {len(self.df['path'].unique())} documents",
                "total_chunks": len(self.df),
                "total_docs": len(self.df["path"].unique()),
                "model": self.model,
            }
        elif self._indexing_task and not self._indexing_task.done():
            return {
                "status": "indexing",
                "message": "Building embeddings in background...",
            }
        else:
            return {"status": "not_started", "message": "Embeddings not initialized"}
