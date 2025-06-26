import os
import shutil

import questionary
import typer
from typing import List
from boilergen.builder.project_setup import create_project
import boilergen.core.template


def ask_for_output_location(selected_templates: List[boilergen.core.template.Template],run_config):
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
            raise ValueError(f"Output directory {output_selection} does already exist. Run with --clear-output to overwrite it.")
    create_project(output_selection,selected_templates,run_config)