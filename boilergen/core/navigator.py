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
    get_breadcrumb_path,
    display_current_selection,
    console
)
from ..cli import clear_shell


def find_all_dependents_recursive(template_id: str, all_templates: Dict[str, Template], selected_ids: List[str]) -> \
        List[str]:
    """
    Find all templates that depend on the given template ID recursively.
    This includes direct dependents and their dependents.
    """
    all_dependents = set()
    to_check = [template_id]

    while to_check:
        current_id = to_check.pop(0)

        # Find direct dependents of current template
        direct_dependents = find_dependents(current_id, all_templates, selected_ids)

        for dep_id in direct_dependents:
            if dep_id not in all_dependents:
                all_dependents.add(dep_id)
                to_check.append(dep_id)  # Check if this dependent has its own dependents

    return list(all_dependents)


def navigate_templates(base_path: str, run_config) -> List[
    Template]:
    """Navigate through template directories with enhanced UX and dependency management."""
    minimal_ui = run_config.minimal_ui
    dependencies_disabled = run_config.disable_dependencies
    current_path = base_path
    selected_template_ids = []
    excluded_template_ids = []  # Track templates user explicitly excluded in --disable-dependencies mode
    navigation_history = []

    # Load all templates for dependency resolution
    all_templates = find_all_templates(base_path)

    while True:
        clear_shell()

        breadcrumb = get_breadcrumb_path(current_path, base_path)
        if minimal_ui:
            print(f"\n{breadcrumb}\n")
        else:
            console.print(f"\n[bold]{breadcrumb}[/bold]\n")

        # Resolve dependencies and get auto-selected templates
        all_required_ids, auto_selected_ids = resolve_dependencies(selected_template_ids, all_templates)

        # In --disable-dependencies mode, filter out explicitly excluded templates
        if dependencies_disabled:
            all_required_ids = [tid for tid in all_required_ids if tid not in excluded_template_ids]
            auto_selected_ids = [tid for tid in auto_selected_ids if tid not in excluded_template_ids]

        selected_templates = [all_templates[tid] for tid in all_required_ids if tid in all_templates]

        # Show current selection
        display_current_selection(selected_templates, auto_selected_ids, all_templates, dependencies_disabled,
                                  minimal_ui)

        if minimal_ui:
            print()
        else:
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
                    status = "✓" if not minimal_ui else "[X]"
                elif is_auto_selected:
                    status = "✓" if not minimal_ui else "[X]"
                else:
                    status = "○" if not minimal_ui else "[ ]"

                title = f"{status} {template.label} ({template.id})"
                if is_auto_selected:
                    title += " *"

                # Show dependencies info
                if template.requires:
                    dep_text = f" -> requires: {', '.join(template.requires)}" if minimal_ui else f" → requires: {', '.join(template.requires)}"
                    title += dep_text

                choices.append(questionary.Choice(
                    title=title,
                    value=("template", template),
                ))

        # Add subdirectories
        if subgroups:
            for subgroup in subgroups:
                folder_icon = "📁"
                choices.append(questionary.Choice(
                    title=f"{folder_icon} {subgroup}",
                    value=("navigate", subgroup),
                ))

        # Add navigation options
        if choices:
            separator = "-" * 40
            choices.append(questionary.Choice(
                title=separator,
                value=("separator", None),
                disabled=True
            ))

        if navigation_history:
            back_text = "<-- Go Back" if minimal_ui else "⬅️  Go Back"
            choices.append(questionary.Choice(
                title=back_text,
                value=("back", None),
            ))

        finish_text = "Finish Selection"
        if selected_templates:
            finish_text += f" ({len(selected_templates)} selected)"
        if not minimal_ui:
            finish_text = "✅ " + finish_text

        choices.append(questionary.Choice(
            title=finish_text,
            value=("finish", None),
        ))

        if not choices or (len(choices) == 1 and choices[0].value[0] == "finish"):
            break

        # Show the selection menu
        if minimal_ui:
            print()
        else:
            console.print()

        try:
            if minimal_ui:
                # Use a simpler style for minimal UI
                selection = questionary.select(
                    "What would you like to do?",
                    choices=choices,
                    use_shortcuts=True,
                ).ask()
            else:
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
            if minimal_ui:
                print("\nSelection cancelled.")
            else:
                console.print("\n[yellow]Selection cancelled.[/yellow]")
            return []

        if not selection:
            break

        action, value = selection

        if action == "template":
            template = value

            if template.id in selected_template_ids:
                # User wants to deselect - check for dependents
                dependents = find_all_dependents_recursive(template.id, all_templates, selected_template_ids)

                if dependents and dependencies_disabled:
                    # Show warning about dependents only in --disable-dependencies mode
                    dependent_names = [all_templates[dep_id].label for dep_id in dependents if dep_id in all_templates]

                    if minimal_ui:
                        print(f"\nWarning: The following templates depend on '{template.label}':")
                        for dep_name in dependent_names:
                            print(f"  - {dep_name}")
                    else:
                        console.print(
                            f"\n[yellow]Warning: The following templates depend on '{template.label}':[/yellow]")
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
                    # Normal mode: automatically remove dependents without prompting
                    selected_template_ids.remove(template.id)

                    # Also remove all dependents automatically
                    if dependents:
                        for dep_id in dependents:
                            if dep_id in selected_template_ids:
                                selected_template_ids.remove(dep_id)

            elif template.id in auto_selected_ids:
                # User is trying to deselect an auto-selected dependency
                if dependencies_disabled:
                    # In --disable-dependencies, allow deselecting auto-selected dependencies
                    # but show warning about potential issues
                    manually_selected_dependents = []
                    for selected_id in selected_template_ids:
                        if selected_id in all_templates:
                            selected_template = all_templates[selected_id]
                            # Check if this manually selected template requires the one being deselected
                            all_deps, _ = resolve_dependencies([selected_id], all_templates)
                            if template.id in all_deps and template.id != selected_id:
                                manually_selected_dependents.append(selected_id)

                    if manually_selected_dependents:
                        dependent_names = [all_templates[dep_id].label for dep_id in manually_selected_dependents]

                        if minimal_ui:
                            print(f"\nWarning: Removing dependency '{template.label}' may cause issues with:")
                            for dep_name in dependent_names:
                                print(f"  - {dep_name}")
                        else:
                            console.print(
                                f"\n[red]Warning: Removing dependency '{template.label}' may cause issues with:[/red]")
                            for dep_name in dependent_names:
                                console.print(f"  - {dep_name}")

                        confirm = questionary.confirm(
                            "Continue anyway? This may cause template conflicts.",
                            default=False
                        ).ask()

                        if confirm:
                            if minimal_ui:
                                print(f"Note: '{template.label}' will be removed. Use caution.")
                                input("Press Enter to continue...")
                            else:
                                console.print(f"[red]Note: '{template.label}' will be removed. Use caution.[/red]")
                                questionary.press_any_key_to_continue("Press any key to continue...").ask()
                            # Add to excluded list to prevent it from being auto-selected again
                            excluded_template_ids.append(template.id)
                else:
                    # Normal mode: prevent deselection of auto-selected dependencies
                    manually_selected_dependents = []
                    for selected_id in selected_template_ids:
                        if selected_id in all_templates:
                            selected_template = all_templates[selected_id]
                            # Check if this manually selected template requires the one being deselected
                            all_deps, _ = resolve_dependencies([selected_id], all_templates)
                            if template.id in all_deps and template.id != selected_id:
                                manually_selected_dependents.append(selected_id)

                    if manually_selected_dependents:
                        dependent_names = [all_templates[dep_id].label for dep_id in manually_selected_dependents]

                        if minimal_ui:
                            print(f"\nCannot deselect '{template.label}' as it's required by:")
                            for dep_name in dependent_names:
                                print(f"  - {dep_name}")
                            print("Deselect those templates first if you want to remove this dependency.")
                            input("Press Enter to continue...")
                        else:
                            console.print(f"\n[yellow]Cannot deselect '{template.label}' as it's required by:[/yellow]")
                            for dep_name in dependent_names:
                                console.print(f"  - {dep_name}")
                            console.print(
                                "[yellow]Deselect those templates first if you want to remove this dependency.[/yellow]")
                            questionary.press_any_key_to_continue("Press any key to continue...").ask()

            else:
                # User wants to select a template that's not currently selected
                # If it was previously excluded, remove from excluded list
                if template.id in excluded_template_ids:
                    excluded_template_ids.remove(template.id)
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

    # In --disable-dependencies mode, filter out explicitly excluded templates from final result
    if dependencies_disabled:
        final_required_ids = [tid for tid in final_required_ids if tid not in excluded_template_ids]

    return [all_templates[tid] for tid in final_required_ids if tid in all_templates]