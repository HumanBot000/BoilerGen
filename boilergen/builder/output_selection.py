import os
import shutil
import stat
from typing import List

import questionary
import typer

import boilergen.core.template
from boilergen.builder.hooks import process_post_generation_hook, process_pre_generation_hook
from boilergen.builder.project_setup import create_project
import boilergen.core.display

def force_remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clear_cloned_repo(template_dir, minimal_ui, console):
    if template_dir.endswith(f"cloned_templates"):
        if minimal_ui:
            print("Removing remote templates...")
        else:
            console.print("[red]Removing remote templates...[/red]")
        shutil.rmtree(template_dir, onerror=force_remove_readonly)


def ask_for_output_location(selected_templates: List[boilergen.core.template.Template], run_config, template_dir):
    output_selection = questionary.prompt(
        [
            {
                "type": "input",
                "name": "output",
                "message": "Where do you want to generate the output?",
                "default": os.path.join(os.getcwd(), "output"),
            }
        ]
    )["output"]
    if not os.path.exists(output_selection):
        os.makedirs(output_selection, exist_ok=True)
    else:
        if run_config.clear_output:
            if typer.confirm(
                    f"Output directory {output_selection} does already exist. Do you want to overwrite it? {typer.style("(This will delete existing data!)", fg=typer.colors.RED)}",
                    default=False
            ):
                try:
                    shutil.rmtree(output_selection)  # recursively delete
                    os.makedirs(output_selection, exist_ok=True)  # recreate clean output dir
                except PermissionError:
                    raise PermissionError(
                        "Permission denied while trying to delete the output directory. Try running with admin privileges.")
        else:
            raise ValueError(
                f"Output directory {output_selection} does already exist. Run with --clear-output to overwrite it.")
    template_dir = os.sep.join(template_dir.split(os.sep)[:-1])
    process_pre_generation_hook(output_selection,template_dir)
    create_project(output_selection, selected_templates, run_config)
    process_post_generation_hook(output_selection,template_dir)
    clear_cloned_repo(template_dir, run_config.minimal_ui, boilergen.core.display.console)
