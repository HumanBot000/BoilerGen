import os
from typing import List
import questionary
from .template_finder import list_subgroups_and_templates
from .display import (
    clear_shell,
    get_breadcrumb_path,
    display_current_selection,
    console
)


def navigate_templates(base_path: str) -> List[str]:
    """Navigate through template directories with enhanced UX."""
    current_path = base_path
    selected_templates = []
    navigation_history = []

    while True:
        # Clear screen for better UX
        clear_shell()

        breadcrumb = get_breadcrumb_path(current_path, base_path)   # Current Location
        console.print(f"\n[bold]{breadcrumb}[/bold]\n")

        # Show current selection
        display_current_selection(selected_templates, base_path)
        console.print()

        subgroups, templates = list_subgroups_and_templates(current_path)

        # Build choices based on what's available
        choices = []

        # Add templates as selectable items
        if templates:
            for template in templates:
                template_path = os.path.join(current_path, template)
                is_selected = template_path in selected_templates
                status = "✓" if is_selected else "○"
                choices.append(questionary.Choice(
                    title=f"{status} {template}",
                    value=("template", template_path),
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
            # No options available, just finish
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
            # Toggle template selection
            if value in selected_templates:
                selected_templates.remove(value)
            else:
                selected_templates.append(value)

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

    return selected_templates
