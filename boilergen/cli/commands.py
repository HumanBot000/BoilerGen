import os
import typer
from rich.panel import Panel
from pathlib import Path
from boilergen.core.navigator import navigate_templates
from boilergen.core.display import display_final_selection, build_directory_tree, console
from boilergen.core.template_finder import find_all_templates, resolve_dependencies

app = typer.Typer(help="🔍 Navigate and select templates from your directory structure")
DEFAULT_TEMPLATE_DIR = os.path.join(os.getcwd(), "boilergen", "templates")


@app.command()
def create(
        template_dir: Path = typer.Argument(
            default=DEFAULT_TEMPLATE_DIR,
            help="Path to the template root directory",
            file_okay=False
        ),
        disable_dependencies: bool = typer.Option(
            False,
            "--disable-dependencies",
            help="Show warnings when deselecting templates with dependencies (expert mode)"
        )
):
    """
    🚀 Create a new project by selecting templates interactively.

    By default, dependencies are handled automatically. Use --disable-dependencies
    to get warnings and manual control over dependency conflicts.
    """
    if not os.path.exists(template_dir):
        console.print(f"[red]Error: Template directory '{template_dir}' does not exist.[/red]")
        raise typer.Exit(1)

    if not os.path.isdir(template_dir):
        console.print(f"[red]Error: '{template_dir}' is not a directory.[/red]")
        raise typer.Exit(1)

    try:
        selected_templates = navigate_templates(template_dir, run_mode=disable_dependencies)

        manually_selected_ids = []  # We don't track this separately in the current implementation
        all_selected_ids = [t.id for t in selected_templates]

        # For display purposes, we'll assume any dependency is auto-selected
        auto_selected_ids = []
        for template in selected_templates:
            for dep_id in template.requires:
                if dep_id in all_selected_ids and dep_id not in manually_selected_ids:
                    auto_selected_ids.append(dep_id)

        display_final_selection(selected_templates, template_dir, auto_selected_ids, run_mode=disable_dependencies)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(0)


@app.command()
def templates(
        template_dir: Path = typer.Argument(
            default=DEFAULT_TEMPLATE_DIR,
            help="Path to the template root directory",
            file_okay=False
        )
):
    """
    🌳 Display a tree view of all available templates.
    """
    template_dir = str(template_dir)
    if not os.path.exists(template_dir):
        console.print(f"[red]Error: Template directory '{template_dir}' does not exist.[/red]")
        raise typer.Exit(1)

    tree_root = build_directory_tree(template_dir, template_dir)

    console.print(Panel(
        tree_root,
        title="Template Directory Structure",
        border_style="blue",
        padding=(1, 2)
    ))