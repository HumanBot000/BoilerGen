import collections
import os
import time
from typing import List, Dict

import questionary
import rainbow_tqdm
import tqdm
import yaml
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Label

from boilergen.builder.generation_logic import generate_file
from boilergen.builder.parser.configs import extract_configs, fetch_yaml_configs, NOT_DEFINED
from boilergen.builder.parser.tags import TemplateFile, extract_tags
from boilergen.core.template import Template
from ..cli import clear_shell
from ..cli.run_config import RunConfig


def sort_templates_by_dependencies(
        templates: List[Template],
        strict: bool = True
) -> List[Template]:
    """
    Sorts templates topologically based on declared dependencies.
    If strict is False (expert mode), missing dependencies are ignored.
    """
    id_map: Dict[str, Template] = {t.id: t for t in templates}
    graph: Dict[str, List[str]] = {t.id: [] for t in templates}
    in_degree: Dict[str, int] = {t.id: 0 for t in templates}

    for t in templates:
        for dep in t.requires:
            if dep not in graph:
                if strict:
                    raise ValueError(f"Missing dependency '{dep}' required by template '{t.id}'")
                else:
                    continue
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


def prepare_objects(output_path: str, selected_templates: List[Template], run_config: RunConfig):
    template_files = []

    for template in sort_templates_by_dependencies(selected_templates, not run_config.disable_dependencies):
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
    return template_files


def cli_config_editor(current_config: dict, file_path: str) -> dict | None:
    lines = [f"{k} = {v}" for k, v in current_config.items()]
    initial_text = "\n".join(lines)
    expected_keys = set(current_config.keys())

    editor = TextArea(
        text=initial_text,
        multiline=True,
        wrap_lines=False,
        scrollbar=True,
        line_numbers=True
    )

    # File path label at top (read-only)
    path_label = Label(
        text=f"File: {file_path}",
        style="class:filepath"
    )

    # Status bar at bottom
    statusbar = Label(
        text="Edit these configurations | Ctrl+S = Confirm",
        style="class:status"
    )

    bindings = KeyBindings()

    @bindings.add("c-s")
    def _(event):
        raw = editor.text
        parsed = {}

        for i, line in enumerate(raw.splitlines(), start=1):
            if "=" not in line:
                statusbar.text = f"Line {i} missing '='."
                return

            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()

            if not k:
                statusbar.text = f"Line {i}: empty key."
                return
            if not v:
                statusbar.text = f"Line {i}: value for '{k}' is empty."
                return
            parsed[k] = v

        parsed_keys = set(parsed.keys())
        if parsed_keys != expected_keys:
            missing = expected_keys - parsed_keys
            extra = parsed_keys - expected_keys
            if missing:
                statusbar.text = f"Missing key(s): {', '.join(missing)}"
            elif extra:
                statusbar.text = f"Unknown key(s): {', '.join(extra)}"
            return

        event.app.exit(result=parsed)

    layout = Layout(HSplit([
        path_label,
        editor,
        statusbar
    ]))

    style = Style.from_dict({
        "status": "reverse",
        "filepath": "bold",
    })

    app = Application(
        layout=layout,
        key_bindings=bindings,
        style=style,
        full_screen=True
    )

    result = app.run()
    return result


def interactive_config_editor(template_files: List[TemplateFile]):
    for file in template_files:
        if len(file.configs) > 0:
            clear_shell()
            new_configs = cli_config_editor({
                e.identifier: e.insertion_value if e.insertion_value != NOT_DEFINED else "" for e in file.configs
            }, file.destination_path)
            for config in file.configs:
                if config.identifier in new_configs:
                    config.cli_value = new_configs[config.identifier]
                else:
                    raise ValueError(f"Missing config value for key '{config.identifier}'")


def create_project(output_path: str, selected_templates: List[Template], run_config: RunConfig):
    clear_shell()
    questionary.press_any_key_to_continue(
        "We will now step through the templates to generate your boilerplate project. Press any key to continue...").ask()
    template_files = prepare_objects(output_path, selected_templates, run_config)
    interactive_config_editor(template_files)
    for file in rainbow_tqdm.tqdm(template_files) if run_config.party_mode else tqdm.tqdm(template_files):
        generate_file(file)
        if run_config.party_mode:
            time.sleep(0.1)
