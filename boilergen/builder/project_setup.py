import collections
from pathlib import Path
import time
from typing import List, Dict, Optional, Any
import yaml
from tqdm import tqdm
import rainbow_tqdm
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Label

from boilergen.builder.parser.injections import parse_injections, run_injections
from boilergen.builder.generation_logic import generate_file_content_data
from boilergen.builder.parser.configs import extract_configs, fetch_yaml_configs, NOT_DEFINED
from boilergen.builder.parser.tags import TemplateFile, extract_tags
from boilergen.core.template import Template
from boilergen.core.ui import get_ui
from boilergen.cli.run_config import RunConfig


def sort_templates_by_dependencies(templates: List[Template], strict: bool = True) -> List[Template]:
    """Sorts templates topologically based on declared dependencies."""
    id_map: Dict[str, Template] = {t.id: t for t in templates}
    graph: Dict[str, List[str]] = {t.id: [] for t in templates}
    in_degree: Dict[str, int] = {t.id: 0 for t in templates}

    for t in templates:
        for dep in t.requires:
            if dep not in id_map:
                if strict: raise ValueError(f"Missing dependency '{dep}' required by '{t.id}'")
                continue
            graph[dep].append(t.id)
            in_degree[t.id] += 1

    queue = collections.deque([tid for tid, degree in in_degree.items() if degree == 0])
    sorted_ids = []
    while queue:
        curr = queue.popleft()
        sorted_ids.append(curr)
        for neighbor in graph[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0: queue.append(neighbor)

    if len(sorted_ids) != len(templates):
        raise ValueError("Cyclic dependency detected among templates")
    return [id_map[tid] for tid in sorted_ids]


def prepare_objects(output_path: Path, selected_templates: List[Template], run_config: RunConfig):
    """Scan selected templates and prepare TemplateFile objects."""
    template_files = []
    sorted_templates = sort_templates_by_dependencies(selected_templates, not run_config.disable_dependencies)

    for template in sorted_templates:
        template_path = Path(template.path)
        yaml_path = template_path / "template.yaml"
        if not yaml_path.is_file():
            raise FileNotFoundError(f"'template.yaml' not found in {template_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        injections_dir = template_path / "injections;"
        
        # Walk through template directory
        for item in template_path.rglob("*"):
            if not item.is_file() or item.name == "template.yaml":
                continue
            
            # Skip injections directory
            try:
                if item.relative_to(injections_dir): continue
            except ValueError: pass

            # Calculate destination path
            # We assume the structure is: template_dir / "template" / ...
            # or directly in template_dir if there is no "template" folder?
            # Existing logic: rel_path.split(os.sep, 1)[1:] -> strips the first part.
            rel_parts = item.relative_to(template_path).parts
            if len(rel_parts) < 2: continue # Should at least have 'template/' and a filename
            
            abstracted_rel_path = Path(*rel_parts[1:])
            dest_path = output_path / abstracted_rel_path

            with open(item, "r", encoding="utf-8") as f:
                content = f.read()
            
            tf = TemplateFile(
                content,
                extract_tags(content),
                extract_configs(content),
                str(dest_path)
            )
            fetch_yaml_configs(tf.configs, yaml_data)
            template_files.append(tf)

        # Handle injections
        if injections_dir.is_dir():
            injections_yaml = injections_dir / "injections.yaml"
            if injections_yaml.is_file():
                with open(injections_yaml, "r", encoding="utf-8") as f:
                    inj_data = yaml.safe_load(f)
                for tf in template_files:
                    tf.injections = parse_injections(inj_data, str(injections_yaml))

    return template_files


def refresh_tags_and_configs_after_injections(template_files: List[TemplateFile]):
    """Refresh tags and configs as content might have shifted after injections."""
    for tf in template_files:
        tf.tags = extract_tags(tf.content)
        new_configs = extract_configs(tf.content)
        old_map = {c.identifier: c for c in tf.configs}
        for nc in new_configs:
            if nc.identifier in old_map:
                nc.yaml_value = old_map[nc.identifier].yaml_value
                nc.cli_value = old_map[nc.identifier].cli_value
        tf.configs = new_configs


def cli_config_editor(current_config: dict, file_path: str) -> dict | None:
    """Interactive editor for template configurations."""
    initial_text = "\n".join([f"{k} = {v}" for k, v in current_config.items()])
    expected_keys = set(current_config.keys())

    editor = TextArea(text=initial_text, multiline=True, scrollbar=True, line_numbers=True)
    path_label = Label(text=f"File: {file_path}", style="class:filepath")
    statusbar = Label(text="Edit configurations | Ctrl+S = Confirm", style="class:status")

    bindings = KeyBindings()
    @bindings.add("c-s")
    def _(event):
        parsed = {}
        for i, line in enumerate(editor.text.splitlines(), 1):
            if "=" not in line:
                statusbar.text = f"Line {i} missing '='."
                return
            k, v = map(str.strip, line.split("=", 1))
            if not k or not v:
                statusbar.text = f"Line {i}: empty key or value."
                return
            parsed[k] = v

        if set(parsed.keys()) != expected_keys:
            statusbar.text = "Keys do not match original configuration."
            return
        event.app.exit(result=parsed)

    app = Application(
        layout=Layout(HSplit([path_label, editor, statusbar])),
        key_bindings=bindings,
        style=Style.from_dict({"status": "reverse", "filepath": "bold"}),
        full_screen=True
    )
    return app.run()


def interactive_config_editor(template_files: List[TemplateFile], ui):
    """Iterate through template files and open editor for those with configs."""
    for tf in template_files:
        if tf.configs:
            ui.clear()
            initial_vals = {c.identifier: (c.insertion_value if c.insertion_value != NOT_DEFINED else "") for c in tf.configs}
            new_vals = cli_config_editor(initial_vals, tf.destination_path)
            if new_vals is None: continue # User cancelled? Or handle error
            for c in tf.configs:
                if c.identifier in new_vals:
                    c.cli_value = new_vals[c.identifier]
                else:
                    raise ValueError(f"Missing config value for '{c.identifier}'")


def create_project(output_path_str: str, selected_templates: List[Template], run_config: RunConfig):
    """Main project generation orchestration."""
    ui = get_ui(run_config.minimal_ui)
    ui.clear()
    ui.press_any_key("We will now step through the templates to generate your project. Press any key to continue...")

    out_path = Path(output_path_str)
    template_files = prepare_objects(out_path, selected_templates, run_config)
    
    run_injections(template_files, run_config, output_path_str)
    refresh_tags_and_configs_after_injections(template_files)
    interactive_config_editor(template_files, ui)

    # File generation with progress bar
    progress = rainbow_tqdm.tqdm(template_files) if run_config.party_mode else tqdm(template_files)
    for tf in progress:
        generate_file_content_data(tf, run_config)
        if run_config.party_mode: time.sleep(0.1)

    ui.clear()
    for tf in template_files:
        dest = Path(tf.destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(tf.content, encoding="utf-8")
    
    ui.success(f"Project generated successfully at: {out_path}")
