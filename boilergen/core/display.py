import os
from typing import List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from .template import Template

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


def display_current_selection(selected_templates: List[Template], auto_selected_ids: List[str],
                              all_templates: Dict[str, Template], run_mode: bool = False):
    """Display currently selected templates in a nice format."""
    if not selected_templates:
        text = Text("📝 No templates selected yet", style="dim")
        console.print(text)
        return

    console.print(f"📝 [bold green]Selected Templates ({len(selected_templates)}):[/bold green]")

    for template in selected_templates:
        marker = "✓"
        style = "green"
        suffix = ""

        if template.id in auto_selected_ids:
            marker = "✓"
            suffix = " *"
            style = "yellow"

        # Check if template has missing dependencies (for --disable-dependencies mode warning)
        missing_deps = []
        if run_mode:
            for dep_id in template.requires:
                if dep_id not in [t.id for t in selected_templates]:
                    missing_deps.append(dep_id)

            if missing_deps:
                console.print(f"       ⚠️ Missing: {', '.join(missing_deps)}", style="red")
        console.print(f"   {marker} {template.label} ({template.id}){suffix}", style=style)


def display_final_selection(selected_templates: List[Template], base_path: str,
                            auto_selected_ids: List[str], run_mode: bool = False):
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
    for template in selected_templates:
        rel_path = os.path.relpath(template.path, base_path)
        dir_path = os.path.dirname(rel_path)

        if dir_path == ".":
            dir_path = "Root"

        if dir_path not in template_groups:
            template_groups[dir_path] = []
        template_groups[dir_path].append(template)

    # Build the tree
    for dir_path, templates in sorted(template_groups.items()):
        if dir_path == "Root":
            branch = tree
        else:
            branch = tree.add(f"📂 {dir_path}")

        for template in sorted(templates, key=lambda t: t.label):
            marker = "📄"
            suffix = ""
            style = ""

            if template.id in auto_selected_ids:
                suffix = " *"
                style = "yellow"

            # Check for missing dependencies in --disable-dependencies mode
            missing_deps = []
            if run_mode:
                for dep_id in template.requires:
                    if dep_id not in [t.id for t in selected_templates]:
                        missing_deps.append(dep_id)

            if missing_deps:
                suffix += f" ⚠️"
                style = "red"

            display_text = f"{marker} {template.label} ({template.id}){suffix}"

            branch.add(display_text, style=style if style else None)

    # Add legend
    legend_parts = []
    if auto_selected_ids:
        legend_parts.append("* = Auto-selected dependency")
    if run_mode:
        legend_parts.append("⚠️ = Missing dependencies (--disable-dependencies)")

    title = f"✅ Selection Complete - {len(selected_templates)} template(s) selected"

    # Fix: Create the panel content properly
    if legend_parts:
        # Create a multi-line content with tree and legend
        from rich.console import Group
        from rich.text import Text

        legend_text = Text("\n" + "\n".join(legend_parts))
        panel_content = Group(tree, legend_text)
    else:
        panel_content = tree

    console.print(Panel(
        panel_content,
        title=title,
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
            tree_node.add(f"📄 {template.label} ({template.id})")

        # Add subdirectories
        for subgroup in subgroups:
            subgroup_path = os.path.join(path, subgroup)
            branch = tree_node.add(f"📂 {subgroup}")
            build_tree(subgroup_path, branch)

    tree_root = Tree(f"📁 {os.path.basename(template_dir)}", style="bold blue")
    build_tree(base_path, tree_root)
    return tree_root