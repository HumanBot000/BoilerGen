from pathlib import Path
from typing import List, Tuple, Dict, Optional
from .template import Template

TEMPLATE_MARKER = "template.yaml"

def list_subgroups_and_templates(path: str) -> Tuple[List[str], List[Template]]:
    """List subdirectories and templates in the given path."""
    subgroups, templates = [], []
    p = Path(path)
    if not p.exists(): return [], []
    
    for entry in p.iterdir():
        if entry.is_dir():
            marker = entry / TEMPLATE_MARKER
            if marker.exists():
                template = Template.from_yaml_file(str(entry))
                if template: templates.append(template)
            else:
                subgroups.append(entry.name)
                
    return sorted(subgroups), sorted(templates, key=lambda t: t.label)

def find_all_templates(base_path: str) -> Dict[str, Template]:
    """Recursively find all templates in the directory structure."""
    templates = {}
    def scan_directory(path: Path):
        subgroups, path_templates = list_subgroups_and_templates(str(path))
        for t in path_templates: templates[t.id] = t
        for s in subgroups: scan_directory(path / s)
        
    scan_directory(Path(base_path))
    return templates

def resolve_dependencies(selected_ids: List[str], all_templates: Dict[str, Template]) -> Tuple[List[str], List[str]]:
    """Resolve template dependencies and return all required IDs and auto-selected IDs."""
    resolved, auto_selected = set(), set()
    to_process = list(selected_ids)

    while to_process:
        tid = to_process.pop(0)
        if tid in resolved: continue
        resolved.add(tid)

        if tid in all_templates:
            for dep in all_templates[tid].requires:
                if dep not in resolved:
                    to_process.append(dep)
                    if dep not in selected_ids: auto_selected.add(dep)

    return list(resolved), list(auto_selected)

def find_dependents(tid: str, all_templates: Dict[str, Template], selected_ids: List[str]) -> List[str]:
    """Find templates that depend on the given ID among selected templates."""
    return [sid for sid in selected_ids if sid in all_templates and tid in all_templates[sid].requires]
