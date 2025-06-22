import os
from typing import List, Tuple, Dict
from .template import Template

TEMPLATE_MARKER = "template.yaml"


def list_subgroups_and_templates(path: str) -> Tuple[List[str], List[Template]]:
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
                    template = Template.from_yaml_file(full_path)
                    if template:
                        templates.append(template)
                else:
                    subgroups.append(entry)
    except FileNotFoundError:
        pass
    return sorted(subgroups), sorted(templates, key=lambda t: t.label)


def find_all_templates(base_path: str) -> Dict[str, Template]:
    """
    Recursively find all templates in the directory structure.

    Returns:
        Dict mapping template IDs to Template objects
    """
    templates = {}

    def scan_directory(path: str):
        subgroups, path_templates = list_subgroups_and_templates(path)

        # Add templates from current directory
        for template in path_templates:
            templates[template.id] = template

        # Recursively scan subdirectories
        for subgroup in subgroups:
            scan_directory(os.path.join(path, subgroup))

    scan_directory(base_path)
    return templates


def resolve_dependencies(selected_template_ids: List[str], all_templates: Dict[str, Template]) -> Tuple[
    List[str], List[str]]:
    """
    Resolve template dependencies and return the complete list of required templates.

    Args:
        selected_template_ids: List of manually selected template IDs
        all_templates: Dict of all available templates

    Returns:
        Tuple of (all_required_ids, auto_selected_ids)
    """
    resolved = set()
    auto_selected = set()
    to_process = list(selected_template_ids)

    while to_process:
        template_id = to_process.pop(0)
        if template_id in resolved:
            continue

        resolved.add(template_id)

        if template_id in all_templates:
            template = all_templates[template_id]
            for dependency in template.requires:
                if dependency not in resolved:
                    to_process.append(dependency)
                    if dependency not in selected_template_ids:
                        auto_selected.add(dependency)

    return list(resolved), list(auto_selected)


def find_dependents(template_id: str, all_templates: Dict[str, Template], selected_ids: List[str]) -> List[str]:
    """
    Find templates that depend on the given template ID among selected templates.

    Args:
        template_id: The template ID to find dependents for
        all_templates: Dict of all available templates
        selected_ids: List of currently selected template IDs

    Returns:
        List of template IDs that depend on the given template
    """
    dependents = []
    for selected_id in selected_ids:
        if selected_id in all_templates:
            template = all_templates[selected_id]
            if template_id in template.requires:
                dependents.append(selected_id)
    return dependents