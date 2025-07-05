"""Utilities for parsing documentation content."""

import re
from typing import Dict, List


def extract_sections(content: str) -> List[Dict[str, str]]:
    """Extract sections from MDX content"""
    sections = []
    lines = content.split('\n')
    
    current_section = None
    current_content = []
    current_level = 0
    
    for line in lines:
        if line.startswith('#'):
            if current_section:
                sections.append({
                    "title": current_section,
                    "level": current_level,
                    "content": '\n'.join(current_content).strip()
                })
            
            current_level = len(line.split()[0])
            current_section = line.lstrip('#').strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Add last section
    if current_section:
        sections.append({
            "title": current_section,
            "level": current_level,
            "content": '\n'.join(current_content).strip()
        })
    
    return sections


def extract_code_blocks(content: str) -> List[Dict[str, str]]:
    """Extract code blocks from MDX content"""
    code_blocks = []
    
    # Pattern to match code blocks with optional language
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for language, code in matches:
        # Try to find description before the code block
        description = ""
        code_index = content.find(f"```{language}\n{code}")
        if code_index > 0:
            # Look for text in the previous few lines
            before_code = content[:code_index].split('\n')[-5:]
            description = ' '.join(line.strip() for line in before_code if line.strip() and not line.startswith('#'))
        
        code_blocks.append({
            "language": language or "python",
            "code": code.strip(),
            "description": description
        })
    
    return code_blocks