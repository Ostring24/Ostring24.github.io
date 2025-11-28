#!/usr/bin/env python3
"""Add front matter to markdown files that don't have it."""

import os
import re
from pathlib import Path
from datetime import datetime

def extract_title_from_content(content):
    """Extract title from first H1 heading."""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"

def has_frontmatter(content):
    """Check if content already has YAML or TOML front matter."""
    return content.startswith('---\n') or content.startswith('+++\n')

def add_frontmatter(filepath):
    """Add YAML front matter to a markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if has_frontmatter(content):
        return False
    
    # Extract title from content
    title = extract_title_from_content(content)
    
    # Use file modification time as date
    mtime = os.path.getmtime(filepath)
    date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    
    # Create front matter
    frontmatter = f"""---
title: "{title}"
date: {date}
draft: false
---

"""
    
    # Prepend front matter
    new_content = frontmatter + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    """Process all markdown files in content/posts."""
    content_dir = Path('content/posts')
    
    if not content_dir.exists():
        print("Error: content/posts directory not found")
        return
    
    md_files = list(content_dir.rglob('*.md'))
    modified = 0
    for filepath in md_files:
        if add_frontmatter(filepath):
            modified += 1
    
    print(f"Added front matter to {modified} files")

if __name__ == '__main__':
    main()
