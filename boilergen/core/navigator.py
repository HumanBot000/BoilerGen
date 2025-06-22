import os
from typing import List, Dict
import questionary
from .template_finder import (
    list_subgroups_and_templates,
    find_all_templates,
    resolve_dependencies,
    find_dependents
)
from .template import Template
from .display import (
    clear_shell,
    get_breadcrumb_path,
    display_current_selection,
    console
)


def navigate_templates(base_path: str, run_mode: bool = False) -> List[Template]:
    """Navigate through template directories with enhanced UX and dependency management."""
    current_path = base_path
    selected_template_ids = []
    navigation_history = []

    # Load all templates for dependency resolution
    all_templates = find_all_templates(base_path)

    while True:
        # Clear screen for better UX
        clear_shell()

        breadcrumb = get_breadcrumb_path(current_path, base_path)
        console.print(f"\n[bold]{breadcrumb}[/bold]\n")

        # Resolve dependencies and get auto-selected templates
        all_required_ids, auto_selected_ids = resolve_dependencies(selected_template_ids, all_templates)
        selected_templates = [all_templates[tid] for tid in all_required_ids if tid in all_templates]

        # Show current selection
        display_current_selection(selected_templates, auto_selected_ids, all_templates, run_mode)
        console.print()

        subgroups, templates = list_subgroups_and_templates(current_path)

        # Build choices based on what's available
        choices = []

        # Add templates as selectable items
        if templates:
            for template in templates:
                is_manually_selected = template.id in selected_template_ids
                is_auto_selected = template.id in auto_selected_ids

                if is_manually_selected:
                    status = "✓"
                elif is_auto_selected:
                    status = "✓"
                else:
                    status = "○"

                title = f"{status} {template.label} ({template.id})"
                if is_auto_selected:
                    title += " *"

                # Show dependencies info
                if template.requires:
                    title += f" → requires: {', '.join(template.requires)}"

                choices.append(questionary.Choice(
                    title=title,
                    value=("template", template),
                ))

        # Add subdirectories
        if subgroups:
            for subgroup in subgroups:
                choices.append(questionary.Choice(
                    title=f"📁 {subgroup}",
                    value=("navigate", subgroup),
                ))

        # Add navigation options
        if choices:
            choices.append(questionary.Choice(
                title="─" * 40,
                value=("separator", None),
                disabled=True
            ))

        if navigation_history:
            choices.append(questionary.Choice(
                title="⬅️  Go Back",
                value=("back", None),
            ))

        choices.append(questionary.Choice(
            title="✅ Finish Selection" + (f" ({len(selected_templates)} selected)" if selected_templates else ""),
            value=("finish", None),
        ))

        if not choices or (len(choices) == 1 and choices[0].value[0] == "finish"):
            break

        # Show the selection menu
        console.print()
        try:
            selection = questionary.select(
                "What would you like to do?",
                choices=choices,
                style=questionary.Style([
                    ('selected', 'fg:#ffffff bg:#0066cc bold'),
                    ('pointer', 'fg:#0066cc bold'),
                    ('question', 'fg:#ff9900 bold'),
                    ('answer', 'fg:#22cc22 bold'),  # Green for manually selected
                    ('highlighted', 'fg:#ffaa00 bold'),  # Yellow/orange for auto-selected
                ]),
                use_shortcuts=True,
            ).ask()
        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled.[/yellow]")
            return []

        if not selection:
            break

        action, value = selection

        if action == "template":
            template = value

            if template.id in selected_template_ids:
                # User wants to deselect - check for dependents
                dependents = find_dependents(template.id, all_templates, selected_template_ids)

                if dependents and not run_mode:
                    # Show warning about dependents
                    dependent_names = [all_templates[dep_id].label for dep_id in dependents if dep_id in all_templates]
                    console.print(f"\n[yellow]Warning: The following templates depend on '{template.label}':[/yellow]")
                    for dep_name in dependent_names:
                        console.print(f"  - {dep_name}")

                    confirm = questionary.confirm(
                        "Do you want to deselect them as well?",
                        default=False
                    ).ask()

                    if confirm:
                        # Remove the template and its dependents
                        selected_template_ids.remove(template.id)
                        for dep_id in dependents:
                            if dep_id in selected_template_ids:
                                selected_template_ids.remove(dep_id)
                    # If not confirmed, do nothing (keep the template selected)
                else:
                    # In run mode or no dependents, just remove
                    selected_template_ids.remove(template.id)
                    if dependents and run_mode:
                        # Also remove dependents in run mode
                        for dep_id in dependents:
                            if dep_id in selected_template_ids:
                                selected_template_ids.remove(dep_id)
            else:
                # User wants to select - add if not auto-selected
                if template.id not in auto_selected_ids:
                    selected_template_ids.append(template.id)

        elif action == "navigate":
            # Navigate to subdirectory
            navigation_history.append(current_path)
            current_path = os.path.join(current_path, value)

        elif action == "back":
            # Go back to previous directory
            if navigation_history:
                current_path = navigation_history.pop()

        elif action == "finish":
            # Finish selection
            break

    # Return the final resolved list of templates
    final_required_ids, _ = resolve_dependencies(selected_template_ids, all_templates)
    return [all_templates[tid] for tid in final_required_ids if tid in all_templates]