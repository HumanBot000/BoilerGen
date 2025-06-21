import os
from typing import List, Tuple

TEMPLATE_MARKER = "template.yaml"


def list_subgroups_and_templates(path: str) -> Tuple[List[str], List[str]]:
    """
    List subdirectories and templates in the given path.

    Args:
        path: Directory path to scan

    Returns:
        Tuple of (subgroups, templates) lists
    """
    subgroups = []
    templates = []
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                if os.path.exists(os.path.join(full_path, TEMPLATE_MARKER)):
                    templates.append(entry)
                else:
                    subgroups.append(entry)
    except FileNotFoundError:
        pass
    return sorted(subgroups), sorted(templates)