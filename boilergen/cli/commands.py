import itertools
import os
from pathlib import Path

import typer
from rich.panel import Panel
from rich.text import Text

from boilergen.cli.run_config import RunConfig
from boilergen.core.display import display_final_selection, console
from boilergen.core.navigator import navigate_templates

app = typer.Typer(help="🔍 Navigate and select templates from your directory structure")
DEFAULT_TEMPLATE_DIR = os.path.join(os.getcwd(), "boilergen", "templates")
RAINBOW_COLORS = ["red", "yellow", "green", "cyan", "blue", "magenta"]


@app.command()
def create(
        template_dir: str = typer.Argument(
            default=DEFAULT_TEMPLATE_DIR,
            help="Path to the template root directory",
            file_okay=False
        ),
        disable_dependencies: bool = typer.Option(
            False,
            "--disable-dependencies",
            help="Show warnings when deselecting templates with dependencies (expert mode)"
        ),
        minimal_ui: bool = typer.Option(
            False,
            "--minimal-ui",
            help="Disable colors and advanced formatting for basic terminal compatibility"
        ),
        clear_output: bool = typer.Option(
            False,
            "--clear-output",
            help="Clear the output directory before generating the project (Deletes existing data!)"
        ),
        party_mode: bool = typer.Option(  # todo hide from --help
            False,
            "--fiesta",

        ),
        disable_quote_parsing: bool = typer.Option(
            False,
            "--disable-quote-parsing",
            help="""By default if there is an " or ' before and after a config value we remove it in the generated project to make type parsing of boilergen configs easier."""
        ),

):
    """
    🚀 Create a new project by selecting templates interactively.
    """
    if not os.path.exists(template_dir):
        if minimal_ui:
            print(f"Error: Template directory '{template_dir}' does not exist.")
        else:
            console.print(f"[red]Error: Template directory '{template_dir}' does not exist.[/red]")
        raise typer.Exit(1)

    if not os.path.isdir(template_dir):
        if minimal_ui:
            print(f"Error: '{template_dir}' is not a directory.")
        else:
            console.print(f"[red]Error: '{template_dir}' is not a directory.[/red]")
        raise typer.Exit(1)

    config = RunConfig(
        disable_dependencies=disable_dependencies,
        minimal_ui=minimal_ui,
        clear_output=clear_output,
        party_mode=party_mode,
        disable_quote_parsing_for_configs=disable_quote_parsing
    )
    try:
        selected_templates = navigate_templates(
            template_dir,
            config
        )

        manually_selected_ids = []  # We don't track this separately in the current implementation
        all_selected_ids = [t.id for t in selected_templates]

        # For display purposes, we'll assume any dependency is auto-selected
        auto_selected_ids = []
        for template in selected_templates:
            for dep_id in template.requires:
                if dep_id in all_selected_ids and dep_id not in manually_selected_ids:
                    auto_selected_ids.append(dep_id)

        display_final_selection(
            selected_templates,
            template_dir,
            auto_selected_ids,
            config
        )

    except KeyboardInterrupt:
        if minimal_ui:
            print("\nOperation cancelled by user.")
        else:
            console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(0)


def generate_simple_tree_text(path: str, prefix="") -> str:
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return prefix + "[Permission Denied]\n"

    tree_lines = []

    filtered_entries = [e for e in entries if e != "template" and e != "template.yaml"]

    for i, entry in enumerate(filtered_entries):
        full_path = os.path.join(path, entry)
        connector = "└── " if i == len(filtered_entries) - 1 else "├── "

        if os.path.isdir(full_path):
            tree_lines.append(prefix + connector + f"📂 {entry}")
            extension = "    " if i == len(filtered_entries) - 1 else "│   "
            subtree = generate_simple_tree_text(full_path, prefix + extension)
            if subtree:
                tree_lines.extend(subtree.splitlines())
        else:
            tree_lines.append(prefix + connector + f"📄 {entry}")

    return "\n".join(tree_lines)


@app.command()
def templates(
        template_dir: Path = typer.Argument(
            default=DEFAULT_TEMPLATE_DIR,
            help="Path to the template root directory",
            file_okay=False
        ),
        minimal_ui: bool = typer.Option(
            False,
            "--minimal-ui",
            help="Disable colors and advanced formatting for basic terminal compatibility"
        ),
        party_mode: bool = typer.Option(
            False,
            "--fiesta",
            help="Display each character in rainbow colors (for fun)"
        )
):
    """
    🌳 Display a tree view of all available templates.
    """
    template_dir = str(template_dir)

    if not os.path.exists(template_dir):
        if minimal_ui:
            print(f"Error: Template directory '{template_dir}' does not exist.")
        else:
            console.print(f"[red]Error: Template directory '{template_dir}' does not exist.[/red]")
        raise typer.Exit(1)

    if minimal_ui and party_mode:
        warning_msg = "[yellow]Warning: --minimal-ui disables colors; fiesta mode will be ignored.[/yellow]"
        console.print(warning_msg)
        party_mode = False

    if party_mode:
        tree_text = generate_simple_tree_text(template_dir)
        rainbow_text = Text()
        color_cycle = itertools.cycle(RAINBOW_COLORS)
        for char in tree_text:
            if char.strip():
                rainbow_text.append(char, style=next(color_cycle))
            else:
                rainbow_text.append(char)
        console.print(Panel(
            rainbow_text,
            title="🎉 Template Directory Structure (Fiesta Mode)",
            border_style="bold magenta",
            padding=(1, 2)
        ))
    else:
        from boilergen.core.display import build_directory_tree
        tree_root = build_directory_tree(template_dir, template_dir, minimal_ui=minimal_ui)

        if minimal_ui:
            print("Template Directory Structure:")
            print("=" * 40)
            print(tree_root)
        else:
            console.print(Panel(
                tree_root,
                title="Template Directory Structure",
                border_style="blue",
                padding=(1, 2)
            ))
