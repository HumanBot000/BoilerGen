from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import questionary
from .template_finder import (
    list_subgroups_and_templates,
    find_all_templates,
    resolve_dependencies,
    find_dependents
)
from .template import Template
from .ui import UI, get_ui


class NavigationController:
    """Controls the template selection navigation flow."""
    
    def __init__(self, base_path: Path, run_config, ui: UI):
        self.base_path = base_path
        self.run_config = run_config
        self.ui = ui
        self.current_path = base_path
        self.selected_ids = []
        self.excluded_ids = []  # Templates explicitly excluded in expert mode
        self.history = []
        self.all_templates = find_all_templates(str(base_path))

    def _get_breadcrumb(self) -> str:
        """Generate a breadcrumb-style path display."""
        try:
            rel_path = self.current_path.relative_to(self.base_path)
            parts = rel_path.parts
            if not parts or parts[0] == ".":
                return "Root Directory"
            return f"Root -> {' -> '.join(parts)}"
        except ValueError:
            return str(self.current_path)

    def navigate(self) -> List[Template]:
        """Main navigation loop."""
        while True:
            self.ui.clear()
            self.ui.print(f"\n[bold]{self._get_breadcrumb()}[/bold]\n" if not self.run_config.minimal_ui else f"\n{self._get_breadcrumb()}\n")

            # Resolve dependencies
            all_req_ids, auto_ids = resolve_dependencies(self.selected_ids, self.all_templates)
            
            if self.run_config.disable_dependencies:
                all_req_ids = [tid for tid in all_req_ids if tid not in self.excluded_ids]
                auto_ids = [tid for tid in auto_ids if tid not in self.excluded_ids]

            current_selection = [self.all_templates[tid] for tid in all_req_ids if tid in self.all_templates]
            self.ui.display_current_selection(current_selection, auto_ids, self.all_templates, self.run_config.disable_dependencies)
            self.ui.print("")

            subgroups, templates = list_subgroups_and_templates(str(self.current_path))
            choices = self._build_choices(templates, subgroups, auto_ids, current_selection)

            if not choices or (len(choices) == 1 and choices[0].value[0] == "finish"):
                break

            selection = self.ui.select("What would you like to do?", choices)
            if not selection: break

            action, value = selection
            if action == "template":
                self._handle_template_selection(value, auto_ids)
            elif action == "navigate":
                self.history.append(self.current_path)
                self.current_path = self.current_path / value
            elif action == "back":
                if self.history: self.current_path = self.history.pop()
            elif action == "finish":
                break

        final_ids, _ = resolve_dependencies(self.selected_ids, self.all_templates)
        if self.run_config.disable_dependencies:
            final_ids = [tid for tid in final_ids if tid not in self.excluded_ids]
        
        return [self.all_templates[tid] for tid in final_ids if tid in self.all_templates]

    def _build_choices(self, templates, subgroups, auto_ids, current_selection) -> List[Any]:
        choices = []
        for t in templates:
            status = ("[X]" if t.id in self.selected_ids or t.id in auto_ids else "[ ]") if self.run_config.minimal_ui else \
                     ("✓" if t.id in self.selected_ids or t.id in auto_ids else "○")
            title = f"{status} {t.label} ({t.id})"
            if t.id in auto_ids: title += " *"
            if t.requires: title += f" {'->' if self.run_config.minimal_ui else '→'} requires: {', '.join(t.requires)}"
            choices.append(questionary.Choice(title=title, value=("template", t)))

        for s in subgroups:
            choices.append(questionary.Choice(title=f"📁 {s}", value=("navigate", s)))

        if choices:
            choices.append(questionary.Choice(title="-" * 40, value=("separator", None), disabled=True))

        if self.history:
            choices.append(questionary.Choice(title=f"{'⬅️  ' if not self.run_config.minimal_ui else '<-- '}Go Back", value=("back", None)))

        finish_text = f"Finish Selection ({len(current_selection)} selected)"
        if not self.run_config.minimal_ui: finish_text = "✅ " + finish_text
        choices.append(questionary.Choice(title=finish_text, value=("finish", None)))
        
        return choices

    def _handle_template_selection(self, template: Template, auto_ids: List[str]):
        if template.id in self.selected_ids:
            self._deselect_template(template)
        elif template.id in auto_ids:
            self._handle_auto_selected_deselection(template)
        else:
            if template.id in self.excluded_ids: self.excluded_ids.remove(template.id)
            self.selected_ids.append(template.id)

    def _deselect_template(self, template: Template):
        dependents = find_all_dependents_recursive(template.id, self.all_templates, self.selected_ids)
        if dependents and self.run_config.disable_dependencies:
            names = [self.all_templates[d].label for d in dependents if d in self.all_templates]
            self.ui.warning(f"The following templates depend on '{template.label}':")
            for n in names: self.ui.print(f"  - {n}")
            if self.ui.confirm("Do you want to deselect them as well?"):
                self.selected_ids.remove(template.id)
                for d in dependents:
                    if d in self.selected_ids: self.selected_ids.remove(d)
        else:
            self.selected_ids.remove(template.id)
            for d in dependents:
                if d in self.selected_ids: self.selected_ids.remove(d)

    def _handle_auto_selected_deselection(self, template: Template):
        if not self.run_config.disable_dependencies:
            # Normal mode: prevent deselection of auto-selected dependencies
            deps = [sid for sid in self.selected_ids if template.id in resolve_dependencies([sid], self.all_templates)[0]]
            if deps:
                names = [self.all_templates[d].label for d in deps if d in self.all_templates]
                self.ui.warning(f"Cannot deselect '{template.label}' as it's required by:")
                for n in names: self.ui.print(f"  - {n}")
                self.ui.press_any_key()
            return

        # Expert mode: allow with warning
        deps = [sid for sid in self.selected_ids if template.id in resolve_dependencies([sid], self.all_templates)[0]]
        if deps:
            names = [self.all_templates[d].label for d in deps if d in self.all_templates]
            self.ui.error(f"Warning: Removing dependency '{template.label}' may cause issues with:")
            for n in names: self.ui.print(f"  - {n}")
            if self.ui.confirm("Continue anyway? This may cause template conflicts."):
                self.excluded_ids.append(template.id)


def find_all_dependents_recursive(template_id: str, all_templates: Dict[str, Template], selected_ids: List[str]) -> List[str]:
    all_deps = set()
    to_check = [template_id]
    while to_check:
        curr = to_check.pop(0)
        direct = find_dependents(curr, all_templates, selected_ids)
        for d in direct:
            if d not in all_deps:
                all_deps.add(d)
                to_check.append(d)
    return list(all_deps)


def navigate_templates(base_path: str, run_config) -> List[Template]:
    """Legacy wrapper for NavigationController."""
    ui = get_ui(run_config.minimal_ui)
    controller = NavigationController(Path(base_path), run_config, ui)
    return controller.navigate()
