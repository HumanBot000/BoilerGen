import collections
import os
from typing import List, Dict

import questionary
import yaml

from boilergen.builder.parser.configs import extract_configs, fetch_yaml_configs
from boilergen.builder.parser.tags import TemplateFile, extract_tags
from boilergen.core.template import Template
from ..cli import clear_shell


def sort_templates_by_dependencies(templates: List[Template]) -> List[Template]:
    """
    Sorts a list of templates based on their dependencies. It guarantees that dependent templates are used after the creation of base templates.
    """
    id_map: Dict[str, Template] = {t.id: t for t in templates}
    graph: Dict[str, List[str]] = {t.id: [] for t in templates}
    in_degree: Dict[str, int] = {t.id: 0 for t in templates}
    for t in templates:
        for dep in t.requires:
            if dep not in graph:
                raise ValueError(f"Missing dependency '{dep}' required by template '{t.id}'")
            graph[dep].append(t.id)
            in_degree[t.id] += 1
    queue = collections.deque([tid for tid, degree in in_degree.items() if degree == 0])
    sorted_ids = []
    while queue:
        current = queue.popleft()
        sorted_ids.append(current)
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(sorted_ids) != len(templates):
        raise ValueError("Cyclic dependency detected among templates")
    return [id_map[tid] for tid in sorted_ids]


def prepare_objects(output_path: str, selected_templates: List[Template]):
    template_files = []

    for template in sort_templates_by_dependencies(selected_templates):
        yaml_path = os.path.join(template.path, "template.yaml")
        if not os.path.isfile(yaml_path):
            raise FileNotFoundError(f"'template.yaml' not found in template: {template.path}")

        with open(yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        for root, dirs, files in os.walk(template.path):
            for file in files:
                if file == "template.yaml":
                    continue

                relative_parts = os.path.relpath(root, template.path).split(os.sep, maxsplit=1)[1:]  # strip template/
                abstracted_path = os.path.join(*relative_parts) if relative_parts else ""
                full_path = os.path.join(root, file)

                with open(full_path, "r") as f:
                    content = f.read()

                template_file = TemplateFile(
                    content,
                    extract_tags(content),
                    extract_configs(content),
                    f"{output_path}{os.sep}{abstracted_path}{os.sep}{file}"
                )
                fetch_yaml_configs(template_file.configs, yaml_data)
                template_files.append(template_file)


def create_project(output_path: str, selected_templates: List[Template]):
    clear_shell()
    questionary.press_any_key_to_continue(
        "We will now step through the templates to generate your boilerplate project. Press any key to continue...").ask()
    prepare_objects(output_path, selected_templates)
