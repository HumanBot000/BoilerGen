import shutil
import stat
from pathlib import Path
from typing import List
from boilergen.builder.hooks import process_post_generation_hook, process_pre_generation_hook
from boilergen.builder.project_setup import create_project
from boilergen.core.template import Template
from boilergen.core.ui import get_ui

def force_remove_readonly(func, path, _):
    """Callback for shutil.rmtree to handle read-only files (common in .git)."""
    Path(path).chmod(stat.S_IWRITE)
    func(path)

def clear_cloned_repo(template_dir: str, minimal_ui: bool, ui):
    """Remove the cloned templates directory if it exists."""
    p = Path(template_dir)
    if p.name == "cloned_templates":
        ui.warning("Removing remote templates...")
        shutil.rmtree(p, onerror=force_remove_readonly)

def ask_for_output_location(selected_templates: List[Template], run_config, template_dir: str):
    """Prompt user for output location and initiate generation."""
    ui = get_ui(run_config.minimal_ui)
    
    default_output = str(Path.cwd() / "output")
    output_path = Path(ui.prompt("Where do you want to generate the output?", default=default_output))

    if not run_config.dry_run:
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
        elif run_config.clear_output:
            if ui.confirm(f"Output directory {output_path} already exists. Overwrite it? (DELETES DATA!)"):
                try:
                    shutil.rmtree(output_path, onerror=force_remove_readonly)
                    output_path.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    ui.error("Permission denied while deleting output directory.")
                    return
        else:
            ui.error(f"Output directory {output_path} already exists. Use --clear-output to overwrite.")
            return

    # template_dir passed here is the 'templates' subdir. Hooks might need the root.
    template_root = Path(template_dir).parent
    
    if not run_config.dry_run:
        process_pre_generation_hook(str(output_path), str(template_root))
    
    create_project(str(output_path), selected_templates, run_config)
    
    if not run_config.dry_run:
        process_post_generation_hook(str(output_path), str(template_root))
    
    clear_cloned_repo(str(template_root), run_config.minimal_ui, ui)
