from typing import List
import questionary
from boilergen.core.template import Template
from ..cli import clear_shell


def create_project(output_path:str,selected_templates:List[Template]):
    clear_shell()
    questionary.press_any_key_to_continue("We will now step through the templates to generate your boilerplate project. Press any key to continue...").ask()