import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from .template import Template

class UI(ABC):
    """Abstract base class for User Interface."""
    
    def clear(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    @abstractmethod
    def display_current_selection(self, selected_templates: List[Template], auto_selected_ids: List[str], 
                                  all_templates: Dict[str, Template], run_mode: bool = False):
        pass
    
    @abstractmethod
    def display_final_selection(self, selected_templates: List[Template], base_path: str, 
                                auto_selected_ids: List[str], run_config):
        pass
    
    @abstractmethod
    def build_directory_tree(self, template_dir: str, base_path: str) -> Any:
        pass

    @abstractmethod
    def select(self, message: str, choices: List[Any], use_shortcuts: bool = True, style: Optional[Any] = None) -> Any:
        pass

    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        pass

    @abstractmethod
    def press_any_key(self, message: str = "Press any key to continue..."):
        pass

    @abstractmethod
    def print(self, message: str, style: Optional[str] = None):
        pass

    @abstractmethod
    def error(self, message: str):
        pass

    @abstractmethod
    def warning(self, message: str):
        pass

    @abstractmethod
    def prompt(self, message: str, default: str = "") -> str:
        pass

    @abstractmethod
    def display_file_content(self, title: str, content: str, lexer: Optional[str] = None):
        pass

    @abstractmethod
    def success(self, message: str):
        pass


class RichUI(UI):
    """Rich-based terminal UI."""
    
    def __init__(self):
        self.console = Console()

    def display_file_content(self, title: str, content: str, lexer: Optional[str] = None):
        from rich.syntax import Syntax
        if lexer is None:
            lexer = "text"
            if "." in title:
                lexer = title.split(".")[-1]
        
        syntax = Syntax(content, lexer, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=f"📄 {title}", border_style="blue", padding=(1, 2)))

    def prompt(self, message: str, default: str = "") -> str:
        return questionary.text(message, default=default).ask()

    def display_current_selection(self, selected_templates: List[Template], auto_selected_ids: List[str], 
                                  all_templates: Dict[str, Template], run_mode: bool = False):
        if not selected_templates:
            self.console.print(Text("📝 No templates selected yet", style="dim"))
            return

        header = f"Selected Templates ({len(selected_templates)}):"
        self.console.print(f"📝 [bold green]{header}[/bold green]")

        for template in selected_templates:
            suffix = " *" if template.id in auto_selected_ids else ""
            
            # Check for missing dependencies
            missing_deps = []
            if run_mode:
                selected_ids = [t.id for t in selected_templates]
                missing_deps = [dep_id for dep_id in template.requires if dep_id not in selected_ids]

            style = "yellow" if template.id in auto_selected_ids else "green"
            self.console.print(f"   ✓ {template.label} ({template.id}){suffix}", style=style)
            
            if missing_deps:
                self.console.print(f"       ⚠️ Missing: {', '.join(missing_deps)}", style="red")

    def display_final_selection(self, selected_templates: List[Template], base_path: str, 
                                auto_selected_ids: List[str], run_config):
        self.clear()
        if not selected_templates:
            self.console.print(Panel.fit(
                "[yellow]No templates were selected.[/yellow]",
                title="Selection Complete",
                border_style="yellow"
            ))
            return

        tree = Tree("📁 Selected Templates", style="bold green")
        template_groups = self._group_templates(selected_templates, base_path)

        for dir_path, templates in sorted(template_groups.items()):
            branch = tree if dir_path == "Root" else tree.add(f"📂 {dir_path}")

            for template in sorted(templates, key=lambda t: t.label):
                suffix = " *" if template.id in auto_selected_ids else ""
                style = "yellow" if template.id in auto_selected_ids else ""

                missing_deps = []
                if run_config.disable_dependencies:
                    selected_ids = [t.id for t in selected_templates]
                    missing_deps = [dep_id for dep_id in template.requires if dep_id not in selected_ids]

                if missing_deps:
                    suffix += " ⚠️"
                    style = "red"

                branch.add(f"📄 {template.label} ({template.id}){suffix}", style=style or None)

        legend_parts = []
        if auto_selected_ids:
            legend_parts.append("* = Auto-selected dependency")
        if run_config.disable_dependencies:
            legend_parts.append("⚠️ = Missing dependencies (--disable-dependencies)")

        title = f"✅ Selection Complete - {len(selected_templates)} template(s) selected"
        
        if legend_parts:
            from rich.console import Group
            legend_text = Text("\n" + "\n".join(legend_parts))
            panel_content = Group(tree, legend_text)
        else:
            panel_content = tree

        self.console.print(Panel(
            panel_content,
            title=title,
            border_style="green",
            padding=(1, 2)
        ))
        print("=" * 50)

    def _group_templates(self, templates: List[Template], base_path: str) -> Dict[str, List[Template]]:
        groups = {}
        for template in templates:
            rel_path = os.path.relpath(template.path, base_path)
            dir_path = os.path.dirname(rel_path)
            if dir_path == ".":
                dir_path = "Root"
            groups.setdefault(dir_path, []).append(template)
        return groups

    def build_directory_tree(self, template_dir: str, base_path: str) -> Tree:
        from .template_finder import list_subgroups_and_templates
        
        def _build(path: str, tree_node: Tree):
            subgroups, templates = list_subgroups_and_templates(path)
            for template in templates:
                tree_node.add(f"📄 {template.label} ({template.id})")
            for subgroup in subgroups:
                branch = tree_node.add(f"📂 {subgroup}")
                _build(os.path.join(path, subgroup), branch)

        tree_root = Tree(f"📁 {os.path.basename(template_dir)}", style="bold blue")
        _build(base_path, tree_root)
        return tree_root

    def select(self, message: str, choices: List[Any], use_shortcuts: bool = True, style: Optional[Any] = None) -> Any:
        if style is None:
            style = questionary.Style([
                ('selected', 'fg:#ffffff bg:#0066cc bold'),
                ('pointer', 'fg:#0066cc bold'),
                ('question', 'fg:#ff9900 bold'),
                ('answer', 'fg:#22cc22 bold'),
                ('highlighted', 'fg:#ffaa00 bold'),
            ])
        return questionary.select(message, choices=choices, style=style, use_shortcuts=use_shortcuts).ask()

    def confirm(self, message: str, default: bool = False) -> bool:
        return questionary.confirm(message, default=default).ask()

    def press_any_key(self, message: str = "Press any key to continue..."):
        questionary.press_any_key_to_continue(message).ask()

    def print(self, message: str, style: Optional[str] = None):
        self.console.print(message, style=style)

    def error(self, message: str):
        self.console.print(f"[red]{message}[/red]")

    def warning(self, message: str):
        self.console.print(f"[yellow]{message}[/yellow]")

    def success(self, message: str):
        self.console.print(f"[green]{message}[/green]")


class MinimalUI(UI):
    """Simple text-based terminal UI."""

    def display_current_selection(self, selected_templates: List[Template], auto_selected_ids: List[str], 
                                  all_templates: Dict[str, Template], run_mode: bool = False):
        if not selected_templates:
            print("No templates selected yet")
            return

        print(f"Selected Templates ({len(selected_templates)}):")
        for template in selected_templates:
            suffix = " *" if template.id in auto_selected_ids else ""
            
            missing_deps = []
            if run_mode:
                selected_ids = [t.id for t in selected_templates]
                missing_deps = [dep_id for dep_id in template.requires if dep_id not in selected_ids]

            print(f"   [X] {template.label} ({template.id}){suffix}")
            if missing_deps:
                print(f"       Warning: Missing: {', '.join(missing_deps)}")

    def display_final_selection(self, selected_templates: List[Template], base_path: str, 
                                auto_selected_ids: List[str], run_config):
        self.clear()
        print("\n" + "=" * 50)
        if not selected_templates:
            print("SELECTION COMPLETE\n" + "=" * 50)
            print("No templates were selected.")
            print("=" * 50)
            return

        print(f"SELECTION COMPLETE - {len(selected_templates)} template(s) selected\n" + "=" * 50)

        # Reusing grouping logic would be good, but for now keeping it simple
        groups = {}
        for template in selected_templates:
            rel_path = os.path.relpath(template.path, base_path)
            dir_path = os.path.dirname(rel_path)
            dir_path = "Root" if dir_path == "." else dir_path
            groups.setdefault(dir_path, []).append(template)

        for dir_path, templates in sorted(groups.items()):
            print(f"\n{dir_path}:")
            for template in sorted(templates, key=lambda t: t.label):
                suffix = " *" if template.id in auto_selected_ids else ""
                if run_config.disable_dependencies:
                    selected_ids = [t.id for t in selected_templates]
                    if any(d not in selected_ids for d in template.requires):
                        suffix += " (WARNING: Missing dependencies)"
                print(f"  - {template.label} ({template.id}){suffix}")

        if auto_selected_ids or run_config.disable_dependencies:
            print("\nLegend:")
            if auto_selected_ids: print("  * = Auto-selected dependency")
            if run_config.disable_dependencies: print("  WARNING = Missing dependencies")

        print("=" * 50)
        print("From here on you will exit --minimal-ui mode")

    def build_directory_tree(self, template_dir: str, base_path: str) -> str:
        from .template_finder import list_subgroups_and_templates
        lines = [f"{os.path.basename(template_dir)}/"]

        def _build(path: str, prefix: str = ""):
            subgroups, templates = list_subgroups_and_templates(path)
            for i, template in enumerate(templates):
                is_last = (i == len(templates) - 1) and not subgroups
                connector = "+-- " if is_last else "|-- "
                lines.append(f"{prefix}{connector}{template.label} ({template.id})")
            for i, subgroup in enumerate(subgroups):
                is_last = i == len(subgroups) - 1
                connector = "+-- " if is_last else "|-- "
                lines.append(f"{prefix}{connector}📂 {subgroup}")
                _build(os.path.join(path, subgroup), prefix + ("    " if is_last else "|   "))

        _build(base_path)
        return "\n".join(lines)

    def select(self, message: str, choices: List[Any], use_shortcuts: bool = True, style: Optional[Any] = None) -> Any:
        return questionary.select(message, choices=choices, use_shortcuts=use_shortcuts).ask()

    def confirm(self, message: str, default: bool = False) -> bool:
        return questionary.confirm(message, default=default).ask()

    def press_any_key(self, message: str = "Press any key to continue..."):
        input(f"\n{message}")

    def print(self, message: str, style: Optional[str] = None):
        print(message)

    def error(self, message: str):
        print(f"Error: {message}")

    def warning(self, message: str):
        print(f"Warning: {message}")

    def success(self, message: str):
        print(f"Success: {message}")

    def display_file_content(self, title: str, content: str, lexer: Optional[str] = None):
        print(f"\n--- 📄 {title} ---")
        print(content)
        print("-" * (len(title) + 10))

    def prompt(self, message: str, default: str = "") -> str:
        return input(f"{message} [{default}]: ") or default


def get_ui(minimal: bool = False) -> UI:
    """Factory function to get the appropriate UI implementation."""
    return MinimalUI() if minimal else RichUI()
