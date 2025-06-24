import yaml
import os
from typing import Dict, List, Any, Optional


class Template:
    def __init__(self, id: str, label: str, requires: List[str] = None, config: Dict[str, Any] = None):
        self.id = id
        self.label = label
        self.requires = requires or []
        self.config = config or {}
        self.path = ""
        self.auto_selected = False  # Flag to track if this was auto-selected as dependency

    @classmethod
    def from_yaml_file(cls, template_path: str) -> Optional['Template']:
        """Load template from a template.yaml file."""
        yaml_path = os.path.join(template_path, "template.yaml")
        if not os.path.exists(yaml_path):
            return None

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            template = cls(
                id=data.get('id', ''),
                label=data.get('label', ''),
                requires=data.get('requires', []),
                config=data.get('config', {})
            )
            template.path = template_path
            return template
        except (yaml.YAMLError, KeyError, FileNotFoundError) as e:
            print(f"Error loading template from {yaml_path}: {e}")
            return None

    def __str__(self):
        return f"Template(id={self.id}, label={self.label}, requires={self.requires})"

    def __repr__(self):
        return self.__str__()