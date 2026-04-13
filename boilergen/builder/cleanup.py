import os
import re
from pathlib import Path

def cleanup_file(file_path: Path):
    """
    Cleans up a single file by:
    - Removing leading and trailing empty lines
    - Collapsing multiple consecutive empty lines into a single one
    """
    if not file_path.is_file():
        return

    try:
        content = file_path.read_text(encoding="utf-8")
        
        # 1. Normalize line endings to \n
        content = content.replace("\r\n", "\n")
        
        # 2. Collapse 3+ consecutive newlines to 2 (one empty line)
        # We use \n\n+ to find 2 or more newlines and replace with exactly two
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 3. Strip leading and trailing whitespace (including newlines)
        content = content.strip()
        
        # 4. Ensure exactly one newline at the end if the file is not empty
        if content:
            content += "\n"
            
        file_path.write_text(content, encoding="utf-8")
    except Exception:
        # Silently skip files that can't be read/written as text
        pass

def cleanup_directory(target_path: Path):
    """Recursively clean up all files in a directory."""
    if not target_path.exists():
        return

    if target_path.is_file():
        cleanup_file(target_path)
        return

    for root, _, files in os.walk(target_path):
        for file in files:
            file_path = Path(root) / file
            cleanup_file(file_path)
