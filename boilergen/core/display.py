import os
from typing import List, Dict

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text

import boilergen.builder.output_selection
from .template import Template
from ..cli import clear_shell

console = Console()


def get_breadcrumb_path(current_path: str, base_path: str) -> str:
    """Generate a breadcrumb-style path display."""
    rel_path = os.path.relpath(current_path, base_path)
    if rel_path == ".":
        return "Root Directory"
    return f"Root -> {rel_path.replace(os.sep, ' -> ')}"


def display_current_selection(selected_templates: List[Template], auto_selected_ids: List[str],
                              all_templates: Dict[str, Template], run_mode: bool = False, minimal_ui: bool = False):
    """Display currently selected templates in a nice format."""
    if not selected_templates:
        if minimal_ui:
            print("No templates selected yet")
        else:
            text = Text("📝 No templates selected yet", style="dim")
            console.print(text)
        return

    header = f"Selected Templates ({len(selected_templates)}):"
    if minimal_ui:
        print(header)
    else:
        console.print(f"📝 [bold green]{header}[/bold green]")

    for template in selected_templates:
        marker = "[X]" if minimal_ui else "✓"
        suffix = ""

        if template.id in auto_selected_ids:
            suffix = " *"

        # Check if template has missing dependencies (for --disable-dependencies mode warning)
        missing_deps = []
        if run_mode:
            for dep_id in template.requires:
                if dep_id not in [t.id for t in selected_templates]:
                    missing_deps.append(dep_id)

        line = f"   {marker} {template.label} ({template.id}){suffix}"

        if minimal_ui:
            print(line)
            if missing_deps:
                print(f"       Warning: Missing: {', '.join(missing_deps)}")
        else:
            if template.id in auto_selected_ids:
                console.print(line, style="yellow")
            else:
                console.print(line, style="green")
            if missing_deps:
                console.print(f"       ⚠️ Missing: {', '.join(missing_deps)}", style="red")


def display_final_selection(selected_templates: List[Template], base_path: str,
                            auto_selected_ids: List[str], run_config):
    """Display the final selection in a nice format."""
    clear_shell()
    if not selected_templates:
        if run_config.minimal_ui:
            print("\n" + "=" * 50)
            print("SELECTION COMPLETE")
            print("=" * 50)
            print("No templates were selected.")
            print("=" * 50)
        else:
            console.print(Panel.fit(
                "[yellow]No templates were selected.[/yellow]",
                title="Selection Complete",
                border_style="yellow"
            ))
        return

    if run_config.minimal_ui:
        print("\n" + "=" * 50)
        print(f"SELECTION COMPLETE - {len(selected_templates)} template(s) selected")
        print("=" * 50)

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

        # Display the grouped templates
        for dir_path, templates in sorted(template_groups.items()):
            if dir_path == "Root":
                print("\nRoot:")
            else:
                print(f"\n{dir_path}:")

            for template in sorted(templates, key=lambda t: t.label):
                suffix = ""

                if template.id in auto_selected_ids:
                    suffix += " *"

                missing_deps = []
                if run_config.disable_dependencies:
                    for dep_id in template.requires:
                        if dep_id not in [t.id for t in selected_templates]:
                            missing_deps.append(dep_id)

                if missing_deps:
                    suffix += " (WARNING: Missing dependencies)"

                print(f"  - {template.label} ({template.id}){suffix}")

        # Add legend
        legend_parts = []
        if auto_selected_ids:
            legend_parts.append("* = Auto-selected dependency")
        if run_config.disable_dependencies:
            legend_parts.append("WARNING = Missing dependencies (--disable-dependencies)")

        if legend_parts:
            print("\nLegend:")
            for legend in legend_parts:
                print(f"  {legend}")

        print("=" * 50)
    else:
        # Rich UI display (existing code)
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
                if run_config.disable_dependencies:
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
        if run_config.disable_dependencies:
            legend_parts.append("⚠️ = Missing dependencies (--disable-dependencies)")

        title = f"✅ Selection Complete - {len(selected_templates)} template(s) selected"

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
    if run_config.minimal_ui:
        print("From here on you will exit --minimal-ui mode")
    else:
        print("=" * 50)
    boilergen.builder.output_selection.ask_for_output_location(selected_templates,run_config,base_path)


def build_directory_tree(template_dir: str, base_path: str, minimal_ui: bool = False) -> str:
    """Build a tree representation of the directory structure."""
    from .template_finder import list_subgroups_and_templates

    if minimal_ui:
        # Simple text-based tree for minimal UI
        lines = []

        def build_simple_tree(path: str, prefix: str = ""):
            subgroups, templates = list_subgroups_and_templates(path)

            # Add templates
            for i, template in enumerate(templates):
                is_last_template = (i == len(templates) - 1) and not subgroups
                connector = "+-- " if is_last_template else "|-- "
                lines.append(f"{prefix}{connector}{template.label} ({template.id})")

            # Add subdirectories
            for i, subgroup in enumerate(subgroups):
                is_last_subgroup = i == len(subgroups) - 1
                connector = "+-- " if is_last_subgroup else "|-- "
                lines.append(f"{prefix}{connector}📂 {subgroup}")

                subgroup_path = os.path.join(path, subgroup)
                extension = "    " if is_last_subgroup else "|   "
                build_simple_tree(subgroup_path, prefix + extension)

        lines.append(f"{os.path.basename(template_dir)}/")
        build_simple_tree(base_path)
        return "\n".join(lines)
    else:
        # Rich tree for normal UI
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