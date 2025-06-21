import os
import typer
from rich.panel import Panel

from core.navigator import navigate_templates
from core.display import display_final_selection, build_directory_tree, console

app = typer.Typer(help="🔍 Navigate and select templates from your directory structure")


@app.command()
def select(
        template_dir: str = typer.Argument(
            ...,
            help="Path to the template root directory"
        ),
):
    """
    🔍 Navigate and select templates from your directory structure.

    This interactive tool helps you browse through template directories
    and select the ones you need for your project.
    """
    if not os.path.exists(template_dir):
        console.print(f"[red]Error: Template directory '{template_dir}' does not exist.[/red]")
        raise typer.Exit(1)

    if not os.path.isdir(template_dir):
        console.print(f"[red]Error: '{template_dir}' is not a directory.[/red]")
        raise typer.Exit(1)

    try:
        selected_templates = navigate_templates(template_dir)
        display_final_selection(selected_templates, template_dir)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(0)


@app.command()
def templates(
        template_dir: str = typer.Argument(
            ...,
            help="Path to the template root directory"
        )
):
    """
    🌳 Display a tree view of all available templates.
    """
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