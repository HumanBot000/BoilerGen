import datetime
import itertools
import os
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.text import Text
import importlib.metadata
import boilergen.builder.output_selection
from boilergen.cli.run_config import RunConfig
from boilergen.core.debug_manager import DebugType
from boilergen.core.ui import get_ui
from boilergen.core.navigator import navigate_templates
from boilergen.core.config_manager import ConfigManager

app = typer.Typer(
    help="🔍 Navigate and select templates from your directory structure",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    add_completion=False
)

DEFAULT_TEMPLATE_DIR = Path.cwd() / "boilergen"
RAINBOW_COLORS = ["red", "yellow", "green", "cyan", "blue", "magenta"]
def version_callback(value: bool):
    if value:
        typer.echo(f"Current boilergen version is {importlib.metadata.version('boilergen')}")
        raise typer.Exit()
@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )
):
    pass

def create_debug_output_file(path:Optional[str]):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n--- DEBUG SESSION STARTED: {datetime.datetime.now()} ---\n")
    except Exception as e:
        typer.echo(f"Failed to create debug output file: {e}")
        raise typer.Exit(1)

@app.command()
def create(
        disable_dependencies: bool = typer.Option(False, "--disable-dependencies",
                                                  help="Expert mode: allow deselecting dependencies"),
        minimal_ui: bool = typer.Option(False, "--minimal-ui", help="Basic terminal compatibility"),
        clear_output: bool = typer.Option(False, "--clear-output", help="Clear output directory first"),
        disable_quote_parsing: bool = typer.Option(False, "--disable-quote-parsing",
                                                   help="Disable automatic quote stripping in configs"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Do not generate files, only show contents"),
        party_mode: bool = typer.Option(False, "--fiesta", help="🎉 Fiesta mode!"),
        debug:Optional[DebugType ]= typer.Option(None, "--debug", help="Debug mode (tags, injections, all)"),
        debug_output : Optional[str] = typer.Option(None, "--debug-output", help="Debug output file path")
):
    """🚀 Create a new project by selecting templates interactively."""
    ui = get_ui(minimal_ui)
    config_mgr = ConfigManager()
    if debug_output and not debug:
        ui.error("--debug-output requires --debug to be set.")
        raise typer.Exit(1)
    if debug_output:
        create_debug_output_file(debug_output)
    try:
        template_dir = config_mgr.resolve_template_dir(str(DEFAULT_TEMPLATE_DIR), ui)
        if not template_dir.exists() or not template_dir.is_dir():
            ui.error(f"Template directory '{template_dir}' does not exist or is not a directory.")
            raise typer.Exit(1)

        run_config = RunConfig(
            disable_dependencies=disable_dependencies,
            minimal_ui=minimal_ui,
            clear_output=clear_output,
            party_mode=party_mode,
            disable_quote_parsing_for_configs=disable_quote_parsing,
            dry_run=dry_run,
            debug_type=debug,
            debug_output=Path(debug_output) if debug_output else None
        )
        # Re-get UI with debug_manager for error logging
        ui = get_ui(minimal_ui, run_config.debug_manager)
        
        selected_templates = navigate_templates(str(template_dir), run_config)
        if not selected_templates:
            ui.warning("Operation cancelled or no templates selected.")
            return

        # Simple heuristic for auto-selected IDs for display
        all_ids = {t.id for t in selected_templates}
        auto_selected_ids = []
        # This is a bit simplified but works for the final display
        for t in selected_templates:
            if any(req in all_ids for req in t.requires):
                # If it's required by something else, it might be auto-selected
                # But we don't have the exact manual list here easily.
                # The navigator knows it, but we returned a flat list.
                pass

        ui.display_final_selection(selected_templates, str(template_dir), auto_selected_ids, run_config)

        if run_config.debug_manager:
            run_config.debug_manager.state_change("general", "Navigation finished, starting output selection.")

        # Start generation flow
        boilergen.builder.output_selection.ask_for_output_location(selected_templates, run_config, str(template_dir))

        if run_config.debug_manager:
            ui.print("\n")
            ui.display_file_content("log", run_config.debug_manager.get_full_log())
            ui.press_any_key("Debug log displayed. Press any key to finish...")

    except KeyboardInterrupt:
        ui.warning("\nOperation cancelled by user.")
        # Try to show logs even on cancel if they exist
        try:
            if 'run_config' in locals() and run_config.debug_manager:
                ui.display_file_content("log (cancelled)", run_config.debug_manager.get_full_log())
                ui.press_any_key("Debug log displayed. Press any key to exit...")
        except:
            pass
        raise typer.Exit(0)



@app.command()
def config():
    """📝 Display the configuration file location and content."""
    config_mgr = ConfigManager()
    ui = get_ui()
    config_path = config_mgr.get_config_path()
    
    ui.print(f"Configuration file: [bold]{config_path}[/bold]")
    if config_path.exists():
        with open(config_path, "r") as f:
            content = f.read()
        ui.display_file_content("boilergen.config", content, lexer="ini")


@app.command()
def templates(
        minimal_ui: bool = typer.Option(False, "--minimal-ui", help="Basic terminal compatibility"),
        party_mode: bool = typer.Option(False, "--fiesta", help="🎉 Fiesta mode!")
):
    """🌳 Display a tree view of all available templates."""
    ui = get_ui(minimal_ui)
    config_mgr = ConfigManager()
    template_dir = config_mgr.resolve_template_dir(str(DEFAULT_TEMPLATE_DIR), ui)

    if not template_dir.exists():
        ui.error(f"Template directory '{template_dir}' does not exist.")
        raise typer.Exit(1)

    if party_mode and not minimal_ui:
        _display_fiesta_tree(template_dir, ui)
    else:
        tree = ui.build_directory_tree(str(template_dir), str(template_dir))
        if minimal_ui:
            ui.print("Template Directory Structure:\n" + "=" * 40)
            ui.print(tree)
        else:
            ui.print(Panel(tree, title="Template Directory Structure", border_style="blue", padding=(1, 2)))

    # Cleanup cloned repo if any
    parent_dir = template_dir.parent
    boilergen.builder.output_selection.clear_cloned_repo(str(parent_dir), minimal_ui, ui)


def _display_fiesta_tree(path: Path, ui):
    tree_text = generate_simple_tree_text(str(path))
    rainbow_text = Text()
    color_cycle = itertools.cycle(RAINBOW_COLORS)
    for char in tree_text:
        rainbow_text.append(char, style=next(color_cycle) if char.strip() else None)

    ui.print(Panel(rainbow_text, title="🎉 Template Directory Structure (Fiesta Mode)", border_style="bold magenta",
                   padding=(1, 2)))


def generate_simple_tree_text(path: str, prefix="") -> str:
    """Helper for fiesta mode and simple tree display."""
    p = Path(path)
    if not p.exists(): return ""

    lines = []
    entries = sorted([e for e in p.iterdir() if e.name not in ["template", "template.yaml"]])

    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        if entry.is_dir():
            lines.append(f"{prefix}{connector}📂 {entry.name}")
            subtree = generate_simple_tree_text(str(entry), prefix + ("    " if i == len(entries) - 1 else "│   "))
            if subtree: lines.extend(subtree.splitlines())
        else:
            lines.append(f"{prefix}{connector}📄 {entry.name}")

    return "\n".join(lines)
