import os

import questionary
import typer
from typing import List
import boilergen.builder.project_setup
import boilergen.core.template


def ask_for_output_location(selected_templates: List[boilergen.core.template.Template]):
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
        if typer.confirm(
            f"Output directory '{output_selection}' does not exist. Do you want to create it?"
        ):
            os.makedirs(output_selection, exist_ok=True)
    boilergen.builder.create_project.create_project(output_selection,selected_templates)