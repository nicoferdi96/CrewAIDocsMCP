"""MDX-aware document parser for semantic chunking."""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class DocumentSection:
    """Represents a section of an MDX document."""
    heading: str
    level: int  # 1, 2, 3, 4 for #, ##, ###, ####
    content: str
    start_line: int
    end_line: int
    code_blocks: List[str]
    special_components: List[str]


@dataclass
class MDXDocument:
    """Represents a parsed MDX document."""
    frontmatter: Dict[str, Any]
    title: str
    description: str
    sections: List[DocumentSection]
    raw_content: str


class MDXParser:
    """Parser for MDX documentation files."""
    
    def __init__(self):
        # Regex patterns
        self.frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL | re.MULTILINE)
        self.heading_pattern = re.compile(r'^(#{1,4})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(\w+)?\s*\n(.*?)\n```', re.DOTALL)
        self.special_component_pattern = re.compile(r'<(Note|Step|Video|Warning|Tip)[^>]*>(.*?)</\1>', re.DOTALL | re.IGNORECASE)
        
    def parse(self, content: str, file_path: str = "") -> MDXDocument:
        """Parse MDX content into structured document."""
        
        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        
        # Remove frontmatter from content
        content_without_frontmatter = self.frontmatter_pattern.sub('', content, count=1)
        
        # Extract title and description
        title = frontmatter.get('title', self._extract_first_heading(content_without_frontmatter) or file_path)
        description = frontmatter.get('description', '')
        
        # Parse sections
        sections = self._parse_sections(content_without_frontmatter)
        
        return MDXDocument(
            frontmatter=frontmatter,
            title=title,
            description=description,
            sections=sections,
            raw_content=content
        )
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from MDX content."""
        match = self.frontmatter_pattern.search(content)
        if not match:
            return {}
        
        frontmatter_text = match.group(1)
        frontmatter = {}
        
        # Simple YAML parsing for common keys
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                frontmatter[key] = value
        
        return frontmatter
    
    def _extract_first_heading(self, content: str) -> Optional[str]:
        """Extract the first heading from content."""
        match = self.heading_pattern.search(content)
        return match.group(2).strip() if match else None
    
    def _parse_sections(self, content: str) -> List[DocumentSection]:
        """Parse content into logical sections based on headings."""
        lines = content.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            heading_match = self.heading_pattern.match(line)
            
            if heading_match:
                # Save previous section if exists
                if current_section:
                    section_content = '\n'.join(current_content).strip()
                    current_section.content = section_content
                    current_section.end_line = i - 1
                    current_section.code_blocks = self._extract_code_blocks(section_content)
                    current_section.special_components = self._extract_special_components(section_content)
                    sections.append(current_section)
                
                # Start new section
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                current_section = DocumentSection(
                    heading=heading_text,
                    level=level,
                    content="",
                    start_line=i,
                    end_line=i,
                    code_blocks=[],
                    special_components=[]
                )
                current_content = []
            else:
                # Add line to current section content
                if current_section or not heading_match:  # Include content before first heading
                    current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            section_content = '\n'.join(current_content).strip()
            current_section.content = section_content
            current_section.end_line = len(lines) - 1
            current_section.code_blocks = self._extract_code_blocks(section_content)
            current_section.special_components = self._extract_special_components(section_content)
            sections.append(current_section)
        elif current_content:
            # Content before any heading
            section_content = '\n'.join(current_content).strip()
            if section_content:
                intro_section = DocumentSection(
                    heading="Introduction",
                    level=0,
                    content=section_content,
                    start_line=0,
                    end_line=len(current_content) - 1,
                    code_blocks=self._extract_code_blocks(section_content),
                    special_components=self._extract_special_components(section_content)
                )
                sections.append(intro_section)
        
        return sections
    
    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from content."""
        matches = self.code_block_pattern.findall(content)
        return [match[1] for match in matches]  # Return just the code content
    
    def _extract_special_components(self, content: str) -> List[str]:
        """Extract special MDX components (Note, Step, etc.)."""
        matches = self.special_component_pattern.findall(content)
        return [f"<{match[0]}>{match[1]}</{match[0]}>" for match in matches]


class SemanticChunker:
    """Creates semantic chunks from parsed MDX documents."""
    
    def __init__(self, 
                 target_chunk_size: int = 600,  # words
                 max_chunk_size: int = 1000,    # words
                 overlap_size: int = 50):       # words
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_document(self, document: MDXDocument, file_path: str = "") -> List[Dict[str, Any]]:
        """Create semantic chunks from an MDX document."""
        chunks = []
        
        # Create chunks based on H2 sections primarily
        h2_groups = self._group_by_h2_sections(document.sections)
        
        for group_idx, (h2_section, subsections) in enumerate(h2_groups):
            # Combine H2 section with its subsections
            combined_content = self._combine_sections([h2_section] + subsections)
            combined_word_count = len(combined_content.split())
            
            if combined_word_count <= self.max_chunk_size:
                # Section fits in one chunk
                chunk = self._create_chunk(
                    document=document,
                    sections=[h2_section] + subsections,
                    content=combined_content,
                    chunk_index=len(chunks),
                    file_path=file_path
                )
                chunks.append(chunk)
            else:
                # Split large sections
                sub_chunks = self._split_large_section(
                    document=document,
                    sections=[h2_section] + subsections,
                    file_path=file_path,
                    base_chunk_index=len(chunks)
                )
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _group_by_h2_sections(self, sections: List[DocumentSection]) -> List[Tuple[DocumentSection, List[DocumentSection]]]:
        """Group sections by H2 headings."""
        groups = []
        current_h2 = None
        current_subsections = []
        
        for section in sections:
            if section.level <= 2:  # H1 or H2
                # Save previous group
                if current_h2:
                    groups.append((current_h2, current_subsections))
                
                # Start new group
                current_h2 = section
                current_subsections = []
            else:
                # H3, H4, etc. - add to current group
                if current_h2:
                    current_subsections.append(section)
                else:
                    # Create a virtual H2 for orphaned subsections
                    virtual_h2 = DocumentSection(
                        heading="Content",
                        level=2,
                        content="",
                        start_line=section.start_line,
                        end_line=section.start_line,
                        code_blocks=[],
                        special_components=[]
                    )
                    groups.append((virtual_h2, [section]))
        
        # Don't forget the last group
        if current_h2:
            groups.append((current_h2, current_subsections))
        
        return groups
    
    def _combine_sections(self, sections: List[DocumentSection]) -> str:
        """Combine multiple sections into a single content string."""
        combined_parts = []
        
        for section in sections:
            if section.level > 0:  # Don't add heading for intro sections
                heading_prefix = "#" * section.level
                combined_parts.append(f"{heading_prefix} {section.heading}")
            
            if section.content.strip():
                combined_parts.append(section.content.strip())
        
        return "\n\n".join(combined_parts)
    
    def _split_large_section(self, document: MDXDocument, sections: List[DocumentSection], 
                           file_path: str, base_chunk_index: int) -> List[Dict[str, Any]]:
        """Split a large section into smaller chunks."""
        chunks = []
        
        # Try to split by H3 sections first
        for i, section in enumerate(sections):
            content = self._combine_sections([section])
            word_count = len(content.split())
            
            if word_count <= self.max_chunk_size:
                chunk = self._create_chunk(
                    document=document,
                    sections=[section],
                    content=content,
                    chunk_index=base_chunk_index + len(chunks),
                    file_path=file_path
                )
                chunks.append(chunk)
            else:
                # Even H3 section is too large - split by paragraphs
                paragraph_chunks = self._split_by_paragraphs(
                    document=document,
                    section=section,
                    file_path=file_path,
                    base_chunk_index=base_chunk_index + len(chunks)
                )
                chunks.extend(paragraph_chunks)
        
        return chunks
    
    def _split_by_paragraphs(self, document: MDXDocument, section: DocumentSection,
                           file_path: str, base_chunk_index: int) -> List[Dict[str, Any]]:
        """Split a section by paragraphs when it's too large."""
        chunks = []
        paragraphs = section.content.split('\n\n')
        current_chunk_paragraphs = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            paragraph_word_count = len(paragraph.split())
            
            # Check if adding this paragraph would exceed max size
            if current_word_count + paragraph_word_count > self.max_chunk_size and current_chunk_paragraphs:
                # Create chunk from current paragraphs
                content = f"# {section.heading}\n\n" + "\n\n".join(current_chunk_paragraphs)
                chunk = self._create_chunk(
                    document=document,
                    sections=[section],
                    content=content,
                    chunk_index=base_chunk_index + len(chunks),
                    file_path=file_path,
                    is_partial=True
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_paragraphs = [paragraph]
                current_word_count = paragraph_word_count
            else:
                current_chunk_paragraphs.append(paragraph)
                current_word_count += paragraph_word_count
        
        # Don't forget the last chunk
        if current_chunk_paragraphs:
            content = f"# {section.heading}\n\n" + "\n\n".join(current_chunk_paragraphs)
            chunk = self._create_chunk(
                document=document,
                sections=[section],
                content=content,
                chunk_index=base_chunk_index + len(chunks),
                file_path=file_path,
                is_partial=True
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, document: MDXDocument, sections: List[DocumentSection], 
                     content: str, chunk_index: int, file_path: str, 
                     is_partial: bool = False) -> Dict[str, Any]:
        """Create a chunk dictionary with metadata."""
        
        # Determine chunk type
        chunk_type = self._determine_chunk_type(sections)
        
        # Create section hierarchy
        section_hierarchy = " > ".join([section.heading for section in sections if section.level > 0])
        
        # Count code blocks and special components
        total_code_blocks = sum(len(section.code_blocks) for section in sections)
        total_special_components = sum(len(section.special_components) for section in sections)
        
        return {
            "path": file_path,
            "title": document.title,
            "description": document.description,
            "category": self._extract_category_from_path(file_path),
            "chunk_index": chunk_index,
            "chunk_type": chunk_type,
            "section_hierarchy": section_hierarchy,
            "heading_level": min(section.level for section in sections) if sections else 0,
            "content": content.strip(),
            "word_count": len(content.split()),
            "has_code_blocks": total_code_blocks > 0,
            "code_block_count": total_code_blocks,
            "has_special_components": total_special_components > 0,
            "special_component_count": total_special_components,
            "is_partial": is_partial,
            "frontmatter": document.frontmatter,
            "combined": f"{document.title}\n\n{content.strip()}"  # For embedding
        }
    
    def _determine_chunk_type(self, sections: List[DocumentSection]) -> str:
        """Determine the type of chunk based on its content."""
        if not sections:
            return "unknown"
        
        # Check content patterns
        combined_content = " ".join(section.content for section in sections).lower()
        
        if any(section.code_blocks for section in sections):
            return "code_example"
        elif "install" in combined_content or "setup" in combined_content:
            return "installation"
        elif any(word in combined_content for word in ["step", "tutorial", "guide", "how to"]):
            return "tutorial"
        elif any(section.level == 1 for section in sections):
            return "overview"
        elif "concept" in combined_content or "definition" in combined_content:
            return "concept"
        elif "api" in combined_content or "reference" in combined_content:
            return "reference"
        else:
            return "content"
    
    def _extract_category_from_path(self, file_path: str) -> str:
        """Extract category from file path."""
        if not file_path:
            return "unknown"
        
        parts = file_path.split('/')
        if len(parts) > 1:
            return parts[-2]  # Parent directory
        return "root"