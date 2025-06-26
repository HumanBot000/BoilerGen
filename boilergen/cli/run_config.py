from dataclasses import dataclass


@dataclass
class RunConfig:
    disable_dependencies: bool = False
    minimal_ui: bool = False
    clear_output: bool = False
    party_mode: bool = False
