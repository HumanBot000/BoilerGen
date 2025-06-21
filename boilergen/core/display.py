import os
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

console = Console()


def clear_shell():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_breadcrumb_path(current_path: str, base_path: str) -> str:
    """Generate a breadcrumb-style path display."""
    rel_path = os.path.relpath(current_path, base_path)
    if rel_path == ".":
        return "📁 Root"
    return f"📁 Root → {rel_path.replace(os.sep, ' → ')}"


def display_current_selection(selected_templates: List[str], base_path: str):
    """Display currently selected templates in a nice format."""
    if not selected_templates:
        console.print("📝 [dim]No templates selected yet[/dim]")
        return

    console.print(f"📝 [bold green]Selected Templates ({len(selected_templates)}):[/bold green]")
    for template in selected_templates:
        rel_path = os.path.relpath(template, base_path)
        console.print(f"   ✓ [green]{rel_path}[/green]")


def display_final_selection(selected_templates: List[str], base_path: str):
    """Display the final selection in a nice format."""
    clear_shell()
    if not selected_templates:
        console.print(Panel.fit(
            "[yellow]No templates were selected.[/yellow]",
            title="Selection Complete",
            border_style="yellow"
        ))
        return

    # Create a tree view of selected templates
    tree = Tree("📁 Selected Templates", style="bold green")

    # Group templates by their directory structure
    template_groups = {}
    for template_path in selected_templates:
        rel_path = os.path.relpath(template_path, base_path)
        dir_path = os.path.dirname(rel_path)
        template_name = os.path.basename(rel_path)

        if dir_path == ".":
            dir_path = "Root"

        if dir_path not in template_groups:
            template_groups[dir_path] = []
        template_groups[dir_path].append(template_name)

    # Build the tree
    for dir_path, templates in sorted(template_groups.items()):
        if dir_path == "Root":
            branch = tree
        else:
            branch = tree.add(f"📂 {dir_path}")

        for template in sorted(templates):
            branch.add(f"📄 {template}")

    console.print(Panel(
        tree,
        title=f"✅ Selection Complete - {len(selected_templates)} template(s) selected",
        border_style="green",
        padding=(1, 2)
    ))


def build_directory_tree(template_dir: str, base_path: str) -> Tree:
    """Build a tree representation of the directory structure."""
    from .template_finder import list_subgroups_and_templates

    def build_tree(path: str, tree_node: Tree):
        subgroups, templates = list_subgroups_and_templates(path)

        # Add templates
        for template in templates:
            tree_node.add(f"📄 {template}")

        # Add subdirectories
        for subgroup in subgroups:
            subgroup_path = os.path.join(path, subgroup)
            branch = tree_node.add(f"📂 {subgroup}")
            build_tree(subgroup_path, branch)

    tree_root = Tree(f"📁 {os.path.basename(template_dir)}", style="bold blue")
    build_tree(base_path, tree_root)
    return tree_root